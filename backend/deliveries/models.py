from datetime import UTC, datetime
from typing import Literal

from beanie import Document
from pydantic import Field


class DeliverySchedule(Document):
    """
    Recurring weekly delivery schedule managed by the factory.
    Only one active schedule document should exist at a time.
    """

    weekdays: list[int] = Field(default_factory=lambda: [0, 3])  # 0=Mon ... 6=Sun; default Sun+Wed (ISO)
    time_of_day: str = "08:00"  # HH:MM in factory timezone
    active: bool = True
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "delivery_schedules"


class Delivery(Document):
    """A single delivery event — either generated from the schedule or created as a one-off."""

    delivery_datetime: datetime  # UTC
    source: Literal["scheduled", "one_off"] = "scheduled"
    schedule_ref_id: str | None = None
    status: Literal["open", "locked", "completed"] = "open"
    reminder_sent: bool = False  # pre-lock reminder dispatched (sent once)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "deliveries"
        indexes = ["delivery_datetime", "status"]
