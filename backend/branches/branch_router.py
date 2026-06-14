from fastapi import APIRouter, Depends, HTTPException, status

from branches import repository
from catalog import repository as catalog_repository
from catalog.schemas import ProductOut
from core.dependencies import require_branch_user
from deliveries import service as delivery_service

# Branch-facing endpoints: a branch can only ever see/edit its own data.
router = APIRouter(prefix="/branch", tags=["branch"])


@router.get("/products", response_model=list[ProductOut])
async def my_products(user: dict = Depends(require_branch_user)) -> list[dict]:
    branch = await repository.get(user["branch_id"])
    if not branch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")

    products = await catalog_repository.list_by_ids(branch.assigned_product_ids)
    # Only active products are shown to the branch.
    return [{"id": str(p.id), "name": p.name, "unit": p.unit, "active": p.active} for p in products if p.active]


@router.get("/deliveries/upcoming")
async def upcoming_delivery(_user: dict = Depends(require_branch_user)) -> dict:
    deliveries = await delivery_service.list_upcoming()
    if not deliveries:
        return {"delivery": None}
    next_del = deliveries[0]
    delivery_obj = await delivery_service.repository.get_delivery(next_del["id"])
    return {
        "delivery": next_del,
        "is_locked": delivery_service.is_locked(delivery_obj) if delivery_obj else True,
    }
