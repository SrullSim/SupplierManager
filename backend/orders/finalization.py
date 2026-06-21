"""
Lock-time finalization and pre-lock reminders.

Run periodically by the scheduler (and callable directly in tests).

At a delivery's 12-hour cutoff:
  - A branch order still in `draft` but with items is AUTO-CONFIRMED.
  - A branch with no order (or an empty one) is finalized as `empty_finalized`.
  - The delivery is moved to `locked`.
  - The factory is notified which branches had no order.

Before the cutoff (within the configured lead time):
  - Each branch is sent a one-time "your order closes soon" reminder.
"""

import logging
from datetime import UTC, datetime, timedelta

from branches import repository as branch_repository
from core.config import settings
from deliveries.models import Delivery
from deliveries.service import cutoff_utc
from notifications import service as notifications
from orders import repository as order_repository
from orders.models import Order

logger = logging.getLogger("finalization")


async def finalize_due_deliveries(now: datetime | None = None) -> dict:
    """Finalize every open delivery whose cutoff has passed. Idempotent."""
    now = now or datetime.now(UTC)
    open_deliveries = await Delivery.find(Delivery.status == "open").to_list()

    result = {"finalized_deliveries": 0, "auto_confirmed": 0, "empty_finalized": 0, "branches_without_order": []}

    for delivery in open_deliveries:
        delivery_dt = delivery.delivery_datetime
        if delivery_dt.tzinfo is None:
            delivery_dt = delivery_dt.replace(tzinfo=UTC)
        if now < cutoff_utc(delivery_dt):
            continue  # not yet at cutoff

        branches = await branch_repository.list_all()
        missing: list[str] = []

        for branch in branches:
            branch_id = str(branch.id)
            order = await order_repository.get_for_branch_delivery(branch_id, str(delivery.id))

            if order and order.items:
                # Has a real order: auto-confirm if the branch never confirmed.
                if order.status != "confirmed":
                    order.status = "confirmed"
                    order.confirmed_at = now
                    await order.save()
                    result["auto_confirmed"] += 1
            else:
                # No order or empty: finalize as empty and flag for the factory.
                if order is None:
                    order = Order(branch_id=branch_id, delivery_id=str(delivery.id), items=[])
                order.status = "empty_finalized"
                await order.save()
                result["empty_finalized"] += 1
                missing.append(branch.name)

        delivery.status = "locked"
        await delivery.save()
        result["finalized_deliveries"] += 1
        result["branches_without_order"].extend(missing)

        if missing:
            logger.info("Delivery %s locked. Branches without order: %s", delivery.id, ", ".join(missing))

    return result


async def send_pre_lock_reminders(now: datetime | None = None) -> int:
    """Send a one-time reminder for deliveries whose cutoff is within the lead window."""
    now = now or datetime.now(UTC)
    lead = timedelta(hours=settings.reminder_lead_hours)

    open_deliveries = await Delivery.find(
        Delivery.status == "open", Delivery.reminder_sent == False  # noqa: E712
    ).to_list()

    reminded = 0
    for delivery in open_deliveries:
        delivery_dt = delivery.delivery_datetime
        if delivery_dt.tzinfo is None:
            delivery_dt = delivery_dt.replace(tzinfo=UTC)
        cutoff = cutoff_utc(delivery_dt)

        # Within the lead window and not yet past the cutoff.
        if cutoff - lead <= now < cutoff:
            branches = await branch_repository.list_all()
            for branch in branches:
                await notifications.send_to_branch(
                    str(branch.id),
                    title="ההזמנה נסגרת בקרוב",
                    body=f"חלון ההזמנה ל{branch.name} נסגר בעוד {settings.reminder_lead_hours} שעות",
                )
            delivery.reminder_sent = True
            await delivery.save()
            reminded += 1

    return reminded


async def run_scheduled_tasks() -> dict:
    """One tick of the scheduler: send reminders, then finalize due deliveries."""
    reminders = await send_pre_lock_reminders()
    finalization = await finalize_due_deliveries()
    return {"reminders_sent": reminders, **finalization}
