from datetime import UTC, datetime
from typing import Literal

from beanie import Document
from pydantic import Field


class User(Document):
    role: Literal["factory_admin", "branch_user"]
    branch_code: str  # login identifier (unique)
    hashed_password: str
    branch_id: str | None = None  # set for branch_user
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "users"
        indexes = ["branch_code"]


class RefreshToken(Document):
    user_id: str
    token_hash: str  # SHA-256 of the raw JWT
    expires_at: datetime
    revoked: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "refresh_tokens"
        indexes = ["token_hash", "user_id"]
