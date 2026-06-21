from zoneinfo import ZoneInfo

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_env: str = "staging"
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Database
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "bakery_orders"

    # Factory
    factory_timezone: str = "Asia/Jerusalem"

    # Bootstrap (prod only, optional)
    bootstrap_admin_code: str = ""
    bootstrap_admin_password: str = ""

    # Notifications
    firebase_credentials_json: str = ""

    # Scheduler & reminders
    scheduler_enabled: bool = True
    scheduler_interval_minutes: int = 5  # how often the finalization/reminder job runs
    reminder_lead_hours: int = 2  # send the pre-lock reminder this long before cutoff

    @field_validator("factory_timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        ZoneInfo(v)  # raises ZoneInfoNotFoundError if invalid
        return v

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.factory_timezone)


settings = Settings()  # type: ignore[call-arg]
