from fastapi import APIRouter, Depends

from core.dependencies import require_branch_user, require_factory_admin
from orders import service
from orders.schemas import DeliverySummaryOut, OrderOut, OrderUpsert

# Branch-facing order endpoints.
branch_router = APIRouter(prefix="/branch/orders", tags=["orders"])

# Factory-facing order summary.
factory_router = APIRouter(prefix="/factory", tags=["orders"])


@branch_router.get("/{delivery_id}", response_model=OrderOut)
async def get_my_order(delivery_id: str, user: dict = Depends(require_branch_user)) -> dict:
    return await service.get_order(user["branch_id"], delivery_id)


@branch_router.put("/{delivery_id}", response_model=OrderOut)
async def upsert_my_order(
    delivery_id: str, body: OrderUpsert, user: dict = Depends(require_branch_user)
) -> dict:
    return await service.upsert_order(user["branch_id"], delivery_id, body.items)


@branch_router.post("/{delivery_id}/confirm", response_model=OrderOut)
async def confirm_my_order(delivery_id: str, user: dict = Depends(require_branch_user)) -> dict:
    return await service.confirm_order(user["branch_id"], delivery_id)


@factory_router.get("/deliveries/{delivery_id}/summary", response_model=DeliverySummaryOut)
async def delivery_order_summary(delivery_id: str, _admin: dict = Depends(require_factory_admin)) -> dict:
    return await service.delivery_summary(delivery_id)
