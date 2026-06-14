"""Delivery schedule & delivery CRUD tests, including generation and cutoff logic."""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest

from deliveries.models import Delivery, DeliverySchedule
from deliveries.service import cutoff_utc, generate_upcoming_deliveries, is_locked


# ── Schedule endpoints ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_default_schedule(http_client, admin_headers):
    resp = await http_client.get("/factory/schedule", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["weekdays"] == [0, 3]  # default Mon+Thu
    assert data["time_of_day"] == "08:00"


@pytest.mark.asyncio
async def test_update_schedule(http_client, admin_headers):
    resp = await http_client.put(
        "/factory/schedule", json={"weekdays": [0, 2, 4], "time_of_day": "07:30"}, headers=admin_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["weekdays"] == [0, 2, 4]
    assert data["time_of_day"] == "07:30"


@pytest.mark.asyncio
async def test_update_schedule_partial(http_client, admin_headers):
    await http_client.put("/factory/schedule", json={"weekdays": [1, 5]}, headers=admin_headers)
    resp = await http_client.put("/factory/schedule", json={"time_of_day": "09:00"}, headers=admin_headers)
    data = resp.json()
    assert data["weekdays"] == [1, 5]
    assert data["time_of_day"] == "09:00"


@pytest.mark.asyncio
async def test_schedule_rejects_invalid_weekday(http_client, admin_headers):
    resp = await http_client.put("/factory/schedule", json={"weekdays": [7]}, headers=admin_headers)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_schedule_rejects_empty_weekdays(http_client, admin_headers):
    resp = await http_client.put("/factory/schedule", json={"weekdays": []}, headers=admin_headers)
    assert resp.status_code == 422


# ── Delivery CRUD ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_one_off_delivery(http_client, admin_headers):
    future_dt = (datetime.now(UTC) + timedelta(days=3)).isoformat()
    resp = await http_client.post("/factory/deliveries", json={"delivery_datetime": future_dt}, headers=admin_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["source"] == "one_off"
    assert data["status"] == "open"
    assert "cutoff_datetime" in data


@pytest.mark.asyncio
async def test_create_delivery_in_past_rejected(http_client, admin_headers):
    past_dt = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    resp = await http_client.post("/factory/deliveries", json={"delivery_datetime": past_dt}, headers=admin_headers)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_list_upcoming_deliveries(http_client, admin_headers):
    dt1 = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    dt2 = (datetime.now(UTC) + timedelta(days=5)).isoformat()
    await http_client.post("/factory/deliveries", json={"delivery_datetime": dt1}, headers=admin_headers)
    await http_client.post("/factory/deliveries", json={"delivery_datetime": dt2}, headers=admin_headers)

    resp = await http_client.get("/factory/deliveries", headers=admin_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


@pytest.mark.asyncio
async def test_update_delivery(http_client, admin_headers):
    future_dt = (datetime.now(UTC) + timedelta(days=2)).isoformat()
    create = await http_client.post("/factory/deliveries", json={"delivery_datetime": future_dt}, headers=admin_headers)
    delivery_id = create.json()["id"]

    resp = await http_client.patch(
        f"/factory/deliveries/{delivery_id}", json={"status": "completed"}, headers=admin_headers
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_get_single_delivery(http_client, admin_headers):
    future_dt = (datetime.now(UTC) + timedelta(days=2)).isoformat()
    create = await http_client.post("/factory/deliveries", json={"delivery_datetime": future_dt}, headers=admin_headers)
    delivery_id = create.json()["id"]

    resp = await http_client.get(f"/factory/deliveries/{delivery_id}", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == delivery_id


# ── Cutoff / lock logic ───────────────────────────────────────────────────────


def test_cutoff_is_12h_before():
    dt = datetime(2025, 7, 10, 8, 0, tzinfo=UTC)
    assert cutoff_utc(dt) == datetime(2025, 7, 9, 20, 0, tzinfo=UTC)


@pytest.mark.asyncio
async def test_is_locked_by_time():
    d = Delivery(delivery_datetime=datetime.now(UTC) + timedelta(hours=1), source="one_off")
    assert is_locked(d)  # 1h from now < 12h cutoff

    d2 = Delivery(delivery_datetime=datetime.now(UTC) + timedelta(hours=24), source="one_off")
    assert not is_locked(d2)  # 24h from now > 12h cutoff


@pytest.mark.asyncio
async def test_is_locked_by_status():
    d = Delivery(delivery_datetime=datetime.now(UTC) + timedelta(days=10), status="locked", source="one_off")
    assert is_locked(d)


# ── Schedule generation ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_generate_upcoming_creates_deliveries():
    schedule = DeliverySchedule(weekdays=[0, 1, 2, 3, 4, 5, 6], time_of_day="08:00")
    await schedule.insert()

    count = await generate_upcoming_deliveries(days_ahead=7)
    assert count >= 1

    all_deliveries = await Delivery.find_all().to_list()
    for d in all_deliveries:
        assert d.source == "scheduled"


@pytest.mark.asyncio
async def test_generate_is_idempotent():
    schedule = DeliverySchedule(weekdays=[0, 1, 2, 3, 4, 5, 6], time_of_day="08:00")
    await schedule.insert()

    first = await generate_upcoming_deliveries(days_ahead=7)
    second = await generate_upcoming_deliveries(days_ahead=7)
    assert second == 0  # no duplicates


@pytest.mark.asyncio
async def test_generate_respects_schedule_days():
    # Only Monday (0)
    schedule = DeliverySchedule(weekdays=[0], time_of_day="08:00")
    await schedule.insert()

    count = await generate_upcoming_deliveries(days_ahead=14)
    all_deliveries = await Delivery.find_all().to_list()

    tz = ZoneInfo("Asia/Jerusalem")
    for d in all_deliveries:
        local = d.delivery_datetime.astimezone(tz)
        assert local.weekday() == 0, f"Expected Monday, got weekday {local.weekday()}"


# ── DST-aware generation ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_generation_across_dst_transition():
    """
    When generating deliveries across a DST transition, the UTC times
    should shift correctly while the local time stays the same.
    Stored datetimes are naive UTC (mongomock strips tzinfo); re-attach UTC before converting.
    """
    tz = ZoneInfo("Asia/Jerusalem")
    schedule = DeliverySchedule(weekdays=[0, 1, 2, 3, 4, 5, 6], time_of_day="08:00")
    await schedule.insert()

    await generate_upcoming_deliveries(days_ahead=7)
    deliveries = await Delivery.find_all().to_list()

    for d in deliveries:
        utc_dt = d.delivery_datetime.replace(tzinfo=UTC) if d.delivery_datetime.tzinfo is None else d.delivery_datetime
        local = utc_dt.astimezone(tz)
        assert local.hour == 8, f"Expected 08:00 local, got {local}"
        assert local.minute == 0


# ── Branch upcoming endpoint ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_branch_sees_upcoming_delivery(http_client, admin_headers, branch_user):
    future_dt = (datetime.now(UTC) + timedelta(days=2)).isoformat()
    await http_client.post("/factory/deliveries", json={"delivery_datetime": future_dt}, headers=admin_headers)

    login = await http_client.post("/auth/login", json={"branch_code": "branch01", "password": "branch1234"})
    branch_token = login.json()["access_token"]
    resp = await http_client.get("/branch/deliveries/upcoming", headers={"Authorization": f"Bearer {branch_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["delivery"] is not None
    assert "is_locked" in data


@pytest.mark.asyncio
async def test_branch_no_upcoming_delivery(http_client, branch_user):
    login = await http_client.post("/auth/login", json={"branch_code": "branch01", "password": "branch1234"})
    branch_token = login.json()["access_token"]
    resp = await http_client.get("/branch/deliveries/upcoming", headers={"Authorization": f"Bearer {branch_token}"})
    assert resp.status_code == 200
    assert resp.json()["delivery"] is None


# ── Authorization ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_branch_cannot_create_delivery(http_client, branch_user):
    login = await http_client.post("/auth/login", json={"branch_code": "branch01", "password": "branch1234"})
    token = login.json()["access_token"]
    future_dt = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    resp = await http_client.post(
        "/factory/deliveries",
        json={"delivery_datetime": future_dt},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
