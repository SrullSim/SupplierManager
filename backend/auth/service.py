from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status

from auth.models import RefreshToken, User
from core.config import settings
from core.security import (
    JWTError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
    verify_password,
)


async def login(branch_code: str, password: str) -> tuple[str, str]:
    user = await User.find_one(User.branch_code == branch_code, User.active == True)  # noqa: E712
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    payload = {"sub": str(user.id), "role": user.role, "branch_id": user.branch_id}
    access = create_access_token(payload)
    refresh = create_refresh_token(payload)

    expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    await RefreshToken(user_id=str(user.id), token_hash=hash_token(refresh), expires_at=expires_at).insert()

    return access, refresh


async def refresh(raw_token: str) -> tuple[str, str]:
    try:
        payload = decode_token(raw_token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Expected refresh token")

    stored = await RefreshToken.find_one(
        RefreshToken.token_hash == hash_token(raw_token),
        RefreshToken.revoked == False,  # noqa: E712
    )
    if not stored or stored.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token invalid or expired")

    # Rotate: revoke old, issue new pair
    stored.revoked = True
    await stored.save()

    token_payload = {"sub": payload["sub"], "role": payload["role"], "branch_id": payload.get("branch_id")}
    new_access = create_access_token(token_payload)
    new_refresh = create_refresh_token(token_payload)

    new_expires = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    await RefreshToken(user_id=payload["sub"], token_hash=hash_token(new_refresh), expires_at=new_expires).insert()

    return new_access, new_refresh


async def logout(raw_token: str) -> None:
    stored = await RefreshToken.find_one(RefreshToken.token_hash == hash_token(raw_token))
    if stored and not stored.revoked:
        stored.revoked = True
        await stored.save()
    # If already revoked or not found, treat as success (idempotent)


async def purge_expired_refresh_tokens() -> int:
    """Called by the scheduler to clean up old tokens."""
    result = await RefreshToken.find(RefreshToken.expires_at < datetime.now(UTC)).delete()
    return result.deleted_count if result else 0
