from datetime import UTC, datetime

from beanie import Document
from pydantic import Field


class Product(Document):
    name: str  # display name, e.g. "challah" / "חלה"
    unit: str  # unit of sale, e.g. "loaf", "tray"
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "products"
        indexes = ["active"]
