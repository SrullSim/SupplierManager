from datetime import UTC, datetime

from fastapi import HTTPException, status

from branches import repository as branch_repository
from catalog import repository as catalog_repository
from deliveries import repository as delivery_repository
from deliveries import service as delivery_service
from orders import repository
from orders.models import Order, OrderItem
from orders.schemas import OrderItemIn


def _to_out(order: Order, delivery_datetime: datetime) -> dict:
    return {
        "id": str(order.id),
        "branch_id": order.branch_id,
        "delivery_id": order.delivery_id,
        "items": [{"product_id": i.product_id, "quantity": i.quantity} for i in order.items],
        "status": order.status,
        "confirmed_at": order.confirmed_at,
        "is_locked": delivery_service.is_locked_dt(delivery_datetime, order.status),
        "cutoff_datetime": delivery_service.cutoff_utc(delivery_datetime),
    }


async def _load_delivery_or_404(delivery_id: str):
    delivery = await delivery_repository.get_delivery(delivery_id)
    if not delivery:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery not found")
    return delivery


async def _validate_items(branch_id: str, items: list[OrderItemIn]) -> list[OrderItem]:
    """Every product must be assigned to this branch AND active. Quantities are merged per product."""
    branch = await branch_repository.get(branch_id)
    if not branch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")

    assigned = set(branch.assigned_product_ids)

    # Merge duplicate product lines by summing quantities.
    merged: dict[str, int] = {}
    for item in items:
        merged[item.product_id] = merged.get(item.product_id, 0) + item.quantity

    product_ids = list(merged.keys())
    if not all(pid in assigned for pid in product_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more products are not assigned to this branch",
        )

    products = await catalog_repository.list_by_ids(product_ids)
    active_ids = {str(p.id) for p in products if p.active}
    if not all(pid in active_ids for pid in product_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more products are inactive or do not exist",
        )

    return [OrderItem(product_id=pid, quantity=qty) for pid, qty in merged.items()]


# ── Branch operations ──────────────────────────────────────────────────────────

async def get_order(branch_id: str, delivery_id: str) -> dict:
    delivery = await _load_delivery_or_404(delivery_id)
    order = await repository.get_for_branch_delivery(branch_id, delivery_id)
    if not order:
        # Return an empty draft view so the UI has something to render.
        empty = Order(branch_id=branch_id, delivery_id=delivery_id, items=[], status="draft")
        return _to_out(empty, delivery.delivery_datetime)
    return _to_out(order, delivery.delivery_datetime)


async def upsert_order(branch_id: str, delivery_id: str, items: list[OrderItemIn], confirm: bool = False) -> dict:
    delivery = await _load_delivery_or_404(delivery_id)

    # The 12-hour lock: branches cannot create/edit after the cutoff.
    if delivery_service.is_locked_dt(delivery.delivery_datetime, delivery.status):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Order is locked: the 12-hour cutoff has passed",
        )

    validated_items = await _validate_items(branch_id, items)
    new_status = "confirmed" if confirm else "draft"
    order = await repository.upsert(branch_id, delivery_id, validated_items, new_status)
    if confirm:
        order.confirmed_at = datetime.now(UTC)
        await order.save()
    return _to_out(order, delivery.delivery_datetime)


async def confirm_order(branch_id: str, delivery_id: str) -> dict:
    delivery = await _load_delivery_or_404(delivery_id)
    if delivery_service.is_locked_dt(delivery.delivery_datetime, delivery.status):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Order is locked: the 12-hour cutoff has passed",
        )

    order = await repository.get_for_branch_delivery(branch_id, delivery_id)
    if not order or not order.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot confirm an empty order")

    order.status = "confirmed"
    order.confirmed_at = datetime.now(UTC)
    await order.save()
    return _to_out(order, delivery.delivery_datetime)


# ── Factory operations ─────────────────────────────────────────────────────────

async def delivery_summary(delivery_id: str) -> dict:
    delivery = await _load_delivery_or_404(delivery_id)
    orders = await repository.list_for_delivery(delivery_id)
    all_branches = await branch_repository.list_all()

    orders_by_branch = {o.branch_id: o for o in orders}
    branch_summaries = []
    without_order = []

    for branch in all_branches:
        branch_id = str(branch.id)
        order = orders_by_branch.get(branch_id)
        if order and order.items:
            branch_summaries.append({
                "branch_id": branch_id,
                "branch_name": branch.name,
                "branch_code": branch.branch_code,
                "status": order.status,
                "items": [{"product_id": i.product_id, "quantity": i.quantity} for i in order.items],
            })
        else:
            without_order.append(branch.name)

    return {
        "delivery_id": delivery_id,
        "delivery_datetime": delivery.delivery_datetime,
        "branches": branch_summaries,
        "branches_without_order": without_order,
    }
