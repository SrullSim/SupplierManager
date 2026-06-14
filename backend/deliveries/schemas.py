from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ScheduleOut(BaseModel):
    id: str
    weekdays: list[int]
    time_of_day: str
    active: bool


class ScheduleUpdate(BaseModel):
    weekdays: list[int] | None = None
    time_of_day: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}$")

    @field_validator("weekdays")
    @classmethod
    def validate_weekdays(cls, v: list[int] | None) -> list[int] | None:
        if v is not None:
            if not v:
                raise ValueError("weekdays must not be empty")
            for d in v:
                if d < 0 or d > 6:
                    raise ValueError("weekday must be 0-6 (Mon-Sun)")
            v = sorted(set(v))
        return v


class DeliveryOut(BaseModel):
    id: str
    delivery_datetime: datetime
    cutoff_datetime: datetime
    source: str
    status: str


class DeliveryCreate(BaseModel):
    delivery_datetime: datetime


class DeliveryUpdate(BaseModel):
    delivery_datetime: datetime | None = None
    status: str | None = Field(default=None, pattern=r"^(open|locked|completed)$")
