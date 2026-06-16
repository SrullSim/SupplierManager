from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status

from core.config import settings
from deliveries import repository
from deliveries.models import Delivery, DeliverySchedule
from deliveries.schemas import DeliveryCreate, DeliveryUpdate, ScheduleUpdate

LOCK_HOURS = 12


def _ensure_utc(dt: datetime) -> datetime:
    """Mongomock may strip tzinfo; treat naive datetimes as UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def cutoff_utc(delivery_datetime: datetime) -> datetime:
    return _ensure_utc(delivery_datetime) - timedelta(hours=LOCK_HOURS)


def is_locked_dt(delivery_datetime: datetime, delivery_status: str = "open") -> bool:
    """Lock check from a raw datetime + status. Used by the orders module."""
    if delivery_status in ("locked", "completed"):
        return True
    return datetime.now(UTC) >= cutoff_utc(delivery_datetime)


def is_locked(delivery: Delivery) -> bool:
    return is_locked_dt(delivery.delivery_datetime, delivery.status)


def _delivery_to_out(d: Delivery) -> dict:
    return {
        "id": str(d.id),
        "delivery_datetime": d.delivery_datetime,
        "cutoff_datetime": cutoff_utc(d.delivery_datetime),
        "source": d.source,
        "status": d.status,
    }


def _schedule_to_out(s: DeliverySchedule) -> dict:
    return {
        "id": str(s.id),
        "weekdays": s.weekdays,
        "time_of_day": s.time_of_day,
        "active": s.active,
    }


# ── Schedule ───────────────────────────────────────────────────────────────────

async def get_schedule() -> dict:
    schedule = await repository.get_active_schedule()
    if not schedule:
        schedule = await repository.upsert_schedule(weekdays=None, time_of_day=None)
    return _schedule_to_out(schedule)


async def update_schedule(data: ScheduleUpdate) -> dict:
    schedule = await repository.upsert_schedule(data.weekdays, data.time_of_day)
    return _schedule_to_out(schedule)


# ── Delivery CRUD ──────────────────────────────────────────────────────────────

async def create_one_off(data: DeliveryCreate) -> dict:
    dt = data.delivery_datetime.replace(tzinfo=UTC) if data.delivery_datetime.tzinfo is None else data.delivery_datetime.astimezone(UTC)
    if dt <= datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Delivery must be in the future")
    delivery = await repository.create_delivery(dt, source="one_off")
    return _delivery_to_out(delivery)


async def list_upcoming() -> list[dict]:
    deliveries = await repository.list_upcoming()
    return [_delivery_to_out(d) for d in deliveries]


async def update_delivery(delivery_id: str, data: DeliveryUpdate) -> dict:
    delivery = await repository.get_delivery(delivery_id)
    if not delivery:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery not found")

    if data.delivery_datetime is not None:
        dt = data.delivery_datetime.replace(tzinfo=UTC) if data.delivery_datetime.tzinfo is None else data.delivery_datetime.astimezone(UTC)
        delivery.delivery_datetime = dt
    if data.status is not None:
        delivery.status = data.status  # type: ignore[assignment]
    await delivery.save()
    return _delivery_to_out(delivery)


async def get_delivery(delivery_id: str) -> dict:
    delivery = await repository.get_delivery(delivery_id)
    if not delivery:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery not found")
    return _delivery_to_out(delivery)


# ── Schedule → Delivery generation ─────────────────────────────────────────────

async def generate_upcoming_deliveries(days_ahead: int = 14) -> int:
    """
    Generate Delivery documents for the next `days_ahead` days
    based on the active recurring schedule. Idempotent — skips
    dates that already have a delivery at the same datetime.
    """
    schedule = await repository.get_active_schedule()
    if not schedule:
        return 0

    tz = ZoneInfo(settings.factory_timezone)
    now_local = datetime.now(tz)
    hour, minute = map(int, schedule.time_of_day.split(":"))

    created = 0
    for offset in range(days_ahead):
        day = now_local.date() + timedelta(days=offset)
        if day.weekday() in schedule.weekdays:
            local_dt = datetime(day.year, day.month, day.day, hour, minute, tzinfo=tz)
            utc_dt = local_dt.astimezone(UTC)
            if utc_dt <= datetime.now(UTC):
                continue
            existing = await repository.find_by_datetime(utc_dt)
            if not existing:
                await repository.create_delivery(utc_dt, source="scheduled", schedule_ref_id=str(schedule.id))
                created += 1

    return created
