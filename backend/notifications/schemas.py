from pydantic import BaseModel, Field


class PushTokenRegister(BaseModel):
    token: str = Field(min_length=1, max_length=4096)
    device_label: str | None = Field(default=None, max_length=128)


class PushTokenOut(BaseModel):
    id: str
    device_label: str | None
