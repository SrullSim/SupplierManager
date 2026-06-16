from datetime import UTC, datetime
from typing import Literal

from beanie import Document
from pydantic import BaseModel, Field


class OrderItem(BaseModel):
    product_id: str
    quantity: int  # validated > 0 at the schema layer


class Order(Document):
    branch_id: str
    delivery_id: str
    items: list[OrderItem] = Field(default_factory=list)
    # draft: being built; confirmed: branch finalized; locked: past cutoff;
    # empty_finalized: cutoff passed with no real order.
    status: Literal["draft", "confirmed", "locked", "empty_finalized"] = "draft"
    confirmed_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "orders"
        # One order per (branch, delivery).
        indexes = [
            [("branch_id", 1), ("delivery_id", 1)],
        ]
