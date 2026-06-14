from datetime import UTC, datetime

from beanie import PydanticObjectId

from deliveries.models import Delivery, DeliverySchedule


def _strip_tz(dt: datetime) -> datetime:
    """MongoDB stores datetimes as UTC without tzinfo; strip for consistent matching."""
    if dt.tzinfo is not None:
        dt = dt.astimezone(UTC).replace(tzinfo=None)
    return dt


# ── Schedule ───────────────────────────────────────────────────────────────────

async def get_active_schedule() -> DeliverySchedule | None:
    return await DeliverySchedule.find_one(DeliverySchedule.active == True)  # noqa: E712


async def upsert_schedule(weekdays: list[int] | None, time_of_day: str | None) -> DeliverySchedule:
    schedule = await get_active_schedule()
    if not schedule:
        schedule = DeliverySchedule()

    if weekdays is not None:
        schedule.weekdays = weekdays
    if time_of_day is not None:
        schedule.time_of_day = time_of_day
    schedule.updated_at = datetime.now(UTC)
    await schedule.save()
    return schedule


# ── Deliveries ─────────────────────────────────────────────────────────────────

async def create_delivery(delivery_datetime: datetime, source: str = "one_off", schedule_ref_id: str | None = None) -> Delivery:
    delivery = Delivery(delivery_datetime=_strip_tz(delivery_datetime), source=source, schedule_ref_id=schedule_ref_id)
    await delivery.insert()
    return delivery


async def get_delivery(delivery_id: str) -> Delivery | None:
    if not PydanticObjectId.is_valid(delivery_id):
        return None
    return await Delivery.get(PydanticObjectId(delivery_id))


async def list_upcoming(from_dt: datetime | None = None) -> list[Delivery]:
    cutoff = _strip_tz(from_dt or datetime.now(UTC))
    return await Delivery.find(
        Delivery.delivery_datetime >= cutoff
    ).sort("+delivery_datetime").to_list()


async def find_by_datetime(dt: datetime) -> Delivery | None:
    return await Delivery.find_one(Delivery.delivery_datetime == _strip_tz(dt))
