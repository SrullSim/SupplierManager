from datetime import UTC, datetime

from orders.models import Order, OrderItem


async def get_for_branch_delivery(branch_id: str, delivery_id: str) -> Order | None:
    return await Order.find_one(Order.branch_id == branch_id, Order.delivery_id == delivery_id)


async def list_for_delivery(delivery_id: str) -> list[Order]:
    return await Order.find(Order.delivery_id == delivery_id).to_list()


async def upsert(branch_id: str, delivery_id: str, items: list[OrderItem], status: str) -> Order:
    order = await get_for_branch_delivery(branch_id, delivery_id)
    if order is None:
        order = Order(branch_id=branch_id, delivery_id=delivery_id)
    order.items = items
    order.status = status  # type: ignore[assignment]
    order.updated_at = datetime.now(UTC)
    await order.save()
    return order
