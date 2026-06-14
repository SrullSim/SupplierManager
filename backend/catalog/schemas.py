from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    unit: str = Field(min_length=1, max_length=32)


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    unit: str | None = Field(default=None, min_length=1, max_length=32)
    active: bool | None = None


class ProductOut(BaseModel):
    id: str
    name: str
    unit: str
    active: bool
