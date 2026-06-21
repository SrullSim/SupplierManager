"""Lock-time finalization: auto-confirm, empty finalize, delivery locking, reminders."""

from datetime import UTC, datetime, timedelta

import pytest

from deliveries.models import Delivery
from orders import repository as order_repository
from orders.finalization import finalize_due_deliveries, send_pre_lock_reminders
from orders.models import Order, OrderItem


async def _make_branch(http_client, admin_headers, code, product_ids=None) -> str:
    resp = await http_client.post(
        "/factory/branches", json={"branch_code": code, "name": f"Branch {code}"}, headers=admin_headers
    )
    branch_id = resp.json()["id"]
    if product_ids:
        await http_client.put(
            f"/factory/branches/{branch_id}/products", json={"product_ids": product_ids}, headers=admin_headers
        )
    return branch_id


async def _make_product(http_client, admin_headers, name="challah") -> str:
    resp = await http_client.post(
        "/factory/products", json={"name": name, "unit": "loaf"}, headers=admin_headers
    )
    return resp.json()["id"]


async def _delivery(hours_from_now: float, status: str = "open") -> str:
    dt = (datetime.now(UTC) + timedelta(hours=hours_from_now)).replace(tzinfo=None)
    d = Delivery(delivery_datetime=dt, source="one_off", status=status)
    await d.insert()
    return str(d.id)


# ── Finalization ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_finalize_empty_creates_empty_finalized(http_client, admin_headers):
    branch_id = await _make_branch(http_client, admin_headers, "fin01")
    delivery_id = await _delivery(hours_from_now=6)  # cutoff = -6h → passed

    result = await finalize_due_deliveries()

    assert result["finalized_deliveries"] == 1
    assert result["empty_finalized"] == 1
    assert "Branch fin01" in result["branches_without_order"]

    order = await order_repository.get_for_branch_delivery(branch_id, delivery_id)
    assert order is not None
    assert order.status == "empty_finalized"

    delivery = await Delivery.get(delivery_id)
    assert delivery.status == "locked"


@pytest.mark.asyncio
async def test_finalize_auto_confirms_draft_with_items(http_client, admin_headers):
    pid = await _make_product(http_client, admin_headers)
    branch_id = await _make_branch(http_client, admin_headers, "fin02", product_ids=[pid])
    delivery_id = await _delivery(hours_from_now=6)

    # A draft order with items, never confirmed by the branch.
    await order_repository.upsert(branch_id, delivery_id, [OrderItem(product_id=pid, quantity=4)], "draft")

    result = await finalize_due_deliveries()
    assert result["auto_confirmed"] == 1

    order = await order_repository.get_for_branch_delivery(branch_id, delivery_id)
    assert order.status == "confirmed"
    assert order.confirmed_at is not None


@pytest.mark.asyncio
async def test_finalize_keeps_already_confirmed(http_client, admin_headers):
    pid = await _make_product(http_client, admin_headers)
    branch_id = await _make_branch(http_client, admin_headers, "fin03", product_ids=[pid])
    delivery_id = await _delivery(hours_from_now=6)
    await order_repository.upsert(branch_id, delivery_id, [OrderItem(product_id=pid, quantity=2)], "confirmed")

    result = await finalize_due_deliveries()
    # Already confirmed → not counted as a new auto-confirm.
    assert result["auto_confirmed"] == 0
    order = await order_repository.get_for_branch_delivery(branch_id, delivery_id)
    assert order.status == "confirmed"


@pytest.mark.asyncio
async def test_finalize_skips_before_cutoff(http_client, admin_headers):
    await _make_branch(http_client, admin_headers, "fin04")
    delivery_id = await _delivery(hours_from_now=48)  # cutoff = +36h → not reached

    result = await finalize_due_deliveries()
    assert result["finalized_deliveries"] == 0

    delivery = await Delivery.get(delivery_id)
    assert delivery.status == "open"


@pytest.mark.asyncio
async def test_finalize_is_idempotent(http_client, admin_headers):
    await _make_branch(http_client, admin_headers, "fin05")
    await _delivery(hours_from_now=6)

    first = await finalize_due_deliveries()
    second = await finalize_due_deliveries()
    assert first["finalized_deliveries"] == 1
    assert second["finalized_deliveries"] == 0  # already locked


# ── Pre-lock reminders ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_reminder_sent_once_within_lead_window(http_client, admin_headers):
    await _make_branch(http_client, admin_headers, "rem01")
    # Cutoff is 1h away (delivery in 13h, lead window default 2h) → within window.
    delivery_id = await _delivery(hours_from_now=13)

    sent_first = await send_pre_lock_reminders()
    assert sent_first == 1

    delivery = await Delivery.get(delivery_id)
    assert delivery.reminder_sent is True

    # Second run: already reminded → no re-send.
    sent_second = await send_pre_lock_reminders()
    assert sent_second == 0


@pytest.mark.asyncio
async def test_no_reminder_outside_lead_window(http_client, admin_headers):
    await _make_branch(http_client, admin_headers, "rem02")
    await _delivery(hours_from_now=48)  # cutoff +36h, far outside the 2h lead window

    sent = await send_pre_lock_reminders()
    assert sent == 0
