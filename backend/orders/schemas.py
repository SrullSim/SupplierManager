from datetime import datetime

from pydantic import BaseModel, Field


class OrderItemIn(BaseModel):
    product_id: str = Field(min_length=1)
    quantity: int = Field(gt=0, le=100000)  # positive integer, sane upper bound


class OrderUpsert(BaseModel):
    items: list[OrderItemIn]


class OrderItemOut(BaseModel):
    product_id: str
    quantity: int


class OrderOut(BaseModel):
    id: str
    branch_id: str
    delivery_id: str
    items: list[OrderItemOut]
    status: str
    confirmed_at: datetime | None
    is_locked: bool
    cutoff_datetime: datetime


class BranchOrderSummary(BaseModel):
    branch_id: str
    branch_name: str
    branch_code: str
    status: str
    items: list[OrderItemOut]


class DeliverySummaryOut(BaseModel):
    delivery_id: str
    delivery_datetime: datetime
    branches: list[BranchOrderSummary]
    branches_without_order: list[str]  # branch names that have no order
