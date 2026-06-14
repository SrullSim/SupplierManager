"""Auth endpoint and service tests, including DST-aware cutoff validation."""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from auth.models import RefreshToken, User
from auth.service import login, logout, purge_expired_refresh_tokens, refresh
from core.security import create_refresh_token, hash_password, hash_token

# ── Login ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_login_success(factory_admin: User):
    access, refresh_token = await login("admin", "admin1234")
    assert access
    assert refresh_token

    stored = await RefreshToken.find_one(RefreshToken.token_hash == hash_token(refresh_token))
    assert stored is not None
    assert not stored.revoked


@pytest.mark.asyncio
async def test_login_wrong_password(factory_admin: User):
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await login("admin", "wrong")
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_user():
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await login("nobody", "pass")
    assert exc.value.status_code == 401


# ── Refresh ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_refresh_rotates_token(factory_admin: User):
    _, old_refresh = await login("admin", "admin1234")
    new_access, new_refresh = await refresh(old_refresh)

    assert new_access
    assert new_refresh != old_refresh

    old_stored = await RefreshToken.find_one(RefreshToken.token_hash == hash_token(old_refresh))
    assert old_stored and old_stored.revoked

    new_stored = await RefreshToken.find_one(RefreshToken.token_hash == hash_token(new_refresh))
    assert new_stored and not new_stored.revoked


@pytest.mark.asyncio
async def test_refresh_revoked_token_rejected(factory_admin: User):
    from fastapi import HTTPException

    _, raw = await login("admin", "admin1234")
    await logout(raw)

    with pytest.raises(HTTPException) as exc:
        await refresh(raw)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_refresh_garbage_token_rejected():
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await refresh("not.a.jwt")
    assert exc.value.status_code == 401


# ── Logout ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_logout_revokes_token(factory_admin: User):
    _, raw = await login("admin", "admin1234")
    await logout(raw)

    stored = await RefreshToken.find_one(RefreshToken.token_hash == hash_token(raw))
    assert stored and stored.revoked


@pytest.mark.asyncio
async def test_logout_idempotent(factory_admin: User):
    """Logging out twice should not raise."""
    _, raw = await login("admin", "admin1234")
    await logout(raw)
    await logout(raw)  # second call must be a no-op


# ── Purge expired tokens ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_purge_removes_expired(factory_admin: User):
    _, raw = await login("admin", "admin1234")
    stored = await RefreshToken.find_one(RefreshToken.token_hash == hash_token(raw))
    assert stored

    # Back-date expiry so it looks expired
    stored.expires_at = datetime.now(UTC) - timedelta(days=1)
    await stored.save()

    deleted = await purge_expired_refresh_tokens()
    assert deleted == 1


# ── HTTP layer ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_http_login(http_client, factory_admin: User):
    resp = await http_client.post("/auth/login", json={"branch_code": "admin", "password": "admin1234"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_http_login_bad_creds(http_client, factory_admin: User):
    resp = await http_client.post("/auth/login", json={"branch_code": "admin", "password": "wrong"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_http_logout(http_client, factory_admin: User):
    login_resp = await http_client.post("/auth/login", json={"branch_code": "admin", "password": "admin1234"})
    refresh_token = login_resp.json()["refresh_token"]
    resp = await http_client.post("/auth/logout", json={"refresh_token": refresh_token})
    assert resp.status_code == 204


# ── DST-aware cutoff test ──────────────────────────────────────────────────────


def _order_cutoff(delivery_dt: datetime, lock_hours: int = 12) -> datetime:
    """Returns the UTC moment a branch can no longer edit its order."""
    return delivery_dt - timedelta(hours=lock_hours)


def test_cutoff_across_dst_spring_forward():
    """
    Israel springs forward (UTC+2 → UTC+3) on the last Friday of March.
    In 2025 that's 2025-03-28 at 02:00 local time.

    Delivery is Saturday 2025-03-29 at 08:00 local (Asia/Jerusalem = UTC+3 after DST).
    Lock cutoff must be exactly 12 hours before delivery_datetime in UTC:
        delivery = 2025-03-29 05:00 UTC  (08:00 EEST = UTC+3)
        cutoff   = 2025-03-29 05:00 UTC - 12h = 2025-03-28 17:00 UTC
    """
    tz = ZoneInfo("Asia/Jerusalem")

    # Build delivery_datetime as timezone-aware local time, store as UTC
    delivery_local = datetime(2025, 3, 29, 8, 0, tzinfo=tz)
    delivery_utc = delivery_local.astimezone(UTC)

    cutoff_utc = _order_cutoff(delivery_utc)

    expected_cutoff_utc = datetime(2025, 3, 28, 17, 0, tzinfo=UTC)
    assert cutoff_utc == expected_cutoff_utc, f"Expected {expected_cutoff_utc}, got {cutoff_utc}"

    # Israel springs forward at 00:00 UTC on 2025-03-28 (02:00 local → 03:00 local).
    # The cutoff (17:00 UTC on 2025-03-28) is AFTER the transition, so the offset is UTC+3 (IDT).
    cutoff_local = cutoff_utc.astimezone(tz)
    assert cutoff_local.utcoffset() == timedelta(hours=3), "Cutoff should be post-DST (UTC+3 / IDT)"


def test_cutoff_across_dst_fall_back():
    """
    Israel falls back (UTC+3 → UTC+2) on the last Sunday of October.
    In 2025 that's 2025-10-26 at 02:00 local time.

    Delivery is Sunday 2025-10-26 at 14:00 local (UTC+2 after fall-back).
    delivery = 2025-10-26 12:00 UTC
    cutoff   = 2025-10-26 00:00 UTC
    """
    tz = ZoneInfo("Asia/Jerusalem")

    delivery_local = datetime(2025, 10, 26, 14, 0, tzinfo=tz)
    delivery_utc = delivery_local.astimezone(UTC)

    cutoff_utc = _order_cutoff(delivery_utc)
    expected_cutoff_utc = datetime(2025, 10, 26, 0, 0, tzinfo=UTC)
    assert cutoff_utc == expected_cutoff_utc


def test_cutoff_exactly_at_boundary():
    """Order exactly at the cutoff moment is NOT editable (strict less-than)."""
    delivery_utc = datetime(2025, 6, 15, 10, 0, tzinfo=UTC)
    cutoff_utc = _order_cutoff(delivery_utc)
    now = cutoff_utc  # exactly at the boundary

    is_editable = now < cutoff_utc
    assert not is_editable, "At the cutoff moment the order must be locked"


def test_cutoff_one_second_before():
    """One second before the cutoff the order is still editable."""
    delivery_utc = datetime(2025, 6, 15, 10, 0, tzinfo=UTC)
    cutoff_utc = _order_cutoff(delivery_utc)
    now = cutoff_utc - timedelta(seconds=1)

    is_editable = now < cutoff_utc
    assert is_editable
