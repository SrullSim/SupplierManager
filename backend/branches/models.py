from datetime import UTC, datetime

from beanie import Document
from pydantic import Field


class Branch(Document):
    branch_code: str  # human-friendly login code, unique
    name: str  # display name, e.g. "Jerusalem Center"
    assigned_product_ids: list[str] = Field(default_factory=list)
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "branches"
        indexes = ["branch_code"]
