from datetime import UTC, datetime

from beanie import Document
from pydantic import Field


class PushToken(Document):
    """
    An FCM device token for a branch. A branch may have several devices,
    so there is one document per (branch_id, token).
    """

    branch_id: str
    token: str
    device_label: str | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "push_tokens"
        indexes = ["branch_id", "token"]
