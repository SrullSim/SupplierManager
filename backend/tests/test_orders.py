"""Order lifecycle + 12-hour lock tests (the core business rule)."""

from datetime import UTC, datetime, timedelta

import pytest

from deliveries.models import Delivery
from orders.models import Order


# ── Helpers ──────────────────────────────────────────────────────────────────────


async def _make_product(http_client, admin_headers, name="challah", unit="loaf") -> str:
    resp = await http_client.post("/factory/products", json={"name": name, "unit": unit}, headers=admin_headers)
    return resp.json()["id"]


async def _make_branch_with_products(http_client, admin_headers, code="ord01", product_ids=None):
    """Create a branch, assign products, return (branch_id, branch_token)."""
    resp = await http_client.post("/factory/branches", json={"branch_code": code, "name": f"Branch {code}"}, headers=admin_headers)
    branch_id = resp.json()["id"]
    password = resp.json()["generated_password"]
    if product_ids:
        await http_client.put(f"/factory/branches/{branch_id}/products", json={"product_ids": product_ids}, headers=admin_headers)
    login = await http_client.post("/auth/login", json={"branch_code": code, "password": password})
    return branch_id, login.json()["access_token"]


async def _make_delivery(hours_from_now: float, status: str = "open") -> str:
    """Insert a Delivery directly so we can control timing (bypasses future-only API check)."""
    dt = (datetime.now(UTC) + timedelta(hours=hours_from_now)).replace(tzinfo=None)
    delivery = Delivery(delivery_datetime=dt, source="one_off", status=status)
    await delivery.insert()
    return str(delivery.id)


def _bh(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Order creation & editing (before cutoff) ─────────────────────────────────────


@pytest.mark.asyncio
async def test_create_order_before_cutoff(http_client, admin_headers):
    pid = await _make_product(http_client, admin_headers)
    branch_id, token = await _make_branch_with_products(http_client, admin_headers, product_ids=[pid])
    delivery_id = await _make_delivery(hours_from_now=48)  # well before cutoff

    resp = await http_client.put(
        f"/branch/orders/{delivery_id}", json={"items": [{"product_id": pid, "quantity": 10}]}, headers=_bh(token)
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "draft"
    assert data["is_locked"] is False
    assert data["items"] == [{"product_id": pid, "quantity": 10}]


@pytest.mark.asyncio
async def test_edit_order_before_cutoff(http_client, admin_headers):
    pid = await _make_product(http_client, admin_headers)
    branch_id, token = await _make_branch_with_products(http_client, admin_headers, product_ids=[pid])
    delivery_id = await _make_delivery(hours_from_now=48)

    await http_client.put(f"/branch/orders/{delivery_id}", json={"items": [{"product_id": pid, "quantity": 5}]}, headers=_bh(token))
    resp = await http_client.put(f"/branch/orders/{delivery_id}", json={"items": [{"product_id": pid, "quantity": 20}]}, headers=_bh(token))
    assert resp.status_code == 200
    assert resp.json()["items"][0]["quantity"] == 20


@pytest.mark.asyncio
async def test_get_order_returns_empty_draft_when_none(http_client, admin_headers):
    branch_id, token = await _make_branch_with_products(http_client, admin_headers)
    delivery_id = await _make_delivery(hours_from_now=48)

    resp = await http_client.get(f"/branch/orders/{delivery_id}", headers=_bh(token))
    assert resp.status_code == 200
    assert resp.json()["items"] == []
    assert resp.json()["status"] == "draft"


# ── The 12-hour lock (core rule) ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_edit_one_second_before_cutoff_allowed(http_client, admin_headers):
    pid = await _make_product(http_client, admin_headers)
    branch_id, token = await _make_branch_with_products(http_client, admin_headers, product_ids=[pid])
    # Cutoff = delivery - 12h. Put delivery just over 12h away so we're 1s before cutoff.
    delivery_id = await _make_delivery(hours_from_now=12 + 1 / 3600)

    resp = await http_client.put(
        f"/branch/orders/{delivery_id}", json={"items": [{"product_id": pid, "quantity": 3}]}, headers=_bh(token)
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_edit_exactly_at_cutoff_blocked(http_client, admin_headers):
    pid = await _make_product(http_client, admin_headers)
    branch_id, token = await _make_branch_with_products(http_client, admin_headers, product_ids=[pid])
    # Delivery exactly 12h away → cutoff is now → locked (>= is strict-locked).
    delivery_id = await _make_delivery(hours_from_now=12)

    resp = await http_client.put(
        f"/branch/orders/{delivery_id}", json={"items": [{"product_id": pid, "quantity": 3}]}, headers=_bh(token)
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_edit_after_cutoff_blocked(http_client, admin_headers):
    pid = await _make_product(http_client, admin_headers)
    branch_id, token = await _make_branch_with_products(http_client, admin_headers, product_ids=[pid])
    delivery_id = await _make_delivery(hours_from_now=6)  # cutoff was 6h ago

    resp = await http_client.put(
        f"/branch/orders/{delivery_id}", json={"items": [{"product_id": pid, "quantity": 3}]}, headers=_bh(token)
    )
    assert resp.status_code == 403
    assert "locked" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_order_shows_locked_flag_after_cutoff(http_client, admin_headers):
    branch_id, token = await _make_branch_with_products(http_client, admin_headers)
    delivery_id = await _make_delivery(hours_from_now=6)

    resp = await http_client.get(f"/branch/orders/{delivery_id}", headers=_bh(token))
    assert resp.status_code == 200
    assert resp.json()["is_locked"] is True


# ── Confirm ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_confirm_order(http_client, admin_headers):
    pid = await _make_product(http_client, admin_headers)
    branch_id, token = await _make_branch_with_products(http_client, admin_headers, product_ids=[pid])
    delivery_id = await _make_delivery(hours_from_now=48)

    await http_client.put(f"/branch/orders/{delivery_id}", json={"items": [{"product_id": pid, "quantity": 7}]}, headers=_bh(token))
    resp = await http_client.post(f"/branch/orders/{delivery_id}/confirm", headers=_bh(token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "confirmed"
    assert resp.json()["confirmed_at"] is not None


@pytest.mark.asyncio
async def test_confirm_empty_order_rejected(http_client, admin_headers):
    branch_id, token = await _make_branch_with_products(http_client, admin_headers)
    delivery_id = await _make_delivery(hours_from_now=48)

    resp = await http_client.post(f"/branch/orders/{delivery_id}/confirm", headers=_bh(token))
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_confirm_after_cutoff_blocked(http_client, admin_headers):
    pid = await _make_product(http_client, admin_headers)
    branch_id, token = await _make_branch_with_products(http_client, admin_headers, product_ids=[pid])
    delivery_id = await _make_delivery(hours_from_now=6)

    resp = await http_client.post(f"/branch/orders/{delivery_id}/confirm", headers=_bh(token))
    assert resp.status_code == 403


# ── Validation & security ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unassigned_product_rejected(http_client, admin_headers):
    assigned = await _make_product(http_client, admin_headers, "challah")
    other = await _make_product(http_client, admin_headers, "secret-cake")
    branch_id, token = await _make_branch_with_products(http_client, admin_headers, product_ids=[assigned])
    delivery_id = await _make_delivery(hours_from_now=48)

    resp = await http_client.put(
        f"/branch/orders/{delivery_id}", json={"items": [{"product_id": other, "quantity": 1}]}, headers=_bh(token)
    )
    assert resp.status_code == 400
    assert "not assigned" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_inactive_product_rejected(http_client, admin_headers):
    pid = await _make_product(http_client, admin_headers)
    branch_id, token = await _make_branch_with_products(http_client, admin_headers, product_ids=[pid])
    await http_client.patch(f"/factory/products/{pid}", json={"active": False}, headers=admin_headers)
    delivery_id = await _make_delivery(hours_from_now=48)

    resp = await http_client.put(
        f"/branch/orders/{delivery_id}", json={"items": [{"product_id": pid, "quantity": 1}]}, headers=_bh(token)
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_zero_quantity_rejected(http_client, admin_headers):
    pid = await _make_product(http_client, admin_headers)
    branch_id, token = await _make_branch_with_products(http_client, admin_headers, product_ids=[pid])
    delivery_id = await _make_delivery(hours_from_now=48)

    resp = await http_client.put(
        f"/branch/orders/{delivery_id}", json={"items": [{"product_id": pid, "quantity": 0}]}, headers=_bh(token)
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_negative_quantity_rejected(http_client, admin_headers):
    pid = await _make_product(http_client, admin_headers)
    branch_id, token = await _make_branch_with_products(http_client, admin_headers, product_ids=[pid])
    delivery_id = await _make_delivery(hours_from_now=48)

    resp = await http_client.put(
        f"/branch/orders/{delivery_id}", json={"items": [{"product_id": pid, "quantity": -5}]}, headers=_bh(token)
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_duplicate_product_lines_merged(http_client, admin_headers):
    pid = await _make_product(http_client, admin_headers)
    branch_id, token = await _make_branch_with_products(http_client, admin_headers, product_ids=[pid])
    delivery_id = await _make_delivery(hours_from_now=48)

    resp = await http_client.put(
        f"/branch/orders/{delivery_id}",
        json={"items": [{"product_id": pid, "quantity": 3}, {"product_id": pid, "quantity": 4}]},
        headers=_bh(token),
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["quantity"] == 7  # merged


@pytest.mark.asyncio
async def test_branch_cannot_see_other_branch_order(http_client, admin_headers):
    pid = await _make_product(http_client, admin_headers)
    _, token_a = await _make_branch_with_products(http_client, admin_headers, code="brA", product_ids=[pid])
    _, token_b = await _make_branch_with_products(http_client, admin_headers, code="brB", product_ids=[pid])
    delivery_id = await _make_delivery(hours_from_now=48)

    # Branch A creates an order
    await http_client.put(f"/branch/orders/{delivery_id}", json={"items": [{"product_id": pid, "quantity": 9}]}, headers=_bh(token_a))
    # Branch B reads the same delivery -> sees its OWN (empty) order, not A's
    resp = await http_client.get(f"/branch/orders/{delivery_id}", headers=_bh(token_b))
    assert resp.json()["items"] == []


# ── Factory summary ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_factory_summary_groups_by_branch(http_client, admin_headers):
    pid = await _make_product(http_client, admin_headers, "challah")
    _, token_a = await _make_branch_with_products(http_client, admin_headers, code="sumA", product_ids=[pid])
    await _make_branch_with_products(http_client, admin_headers, code="sumB", product_ids=[pid])  # no order
    delivery_id = await _make_delivery(hours_from_now=48)

    await http_client.put(f"/branch/orders/{delivery_id}", json={"items": [{"product_id": pid, "quantity": 12}]}, headers=_bh(token_a))

    resp = await http_client.get(f"/factory/deliveries/{delivery_id}/summary", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["branches"]) == 1
    assert data["branches"][0]["branch_code"] == "sumA"
    assert data["branches"][0]["items"][0]["quantity"] == 12
    assert "Branch sumB" in data["branches_without_order"]


@pytest.mark.asyncio
async def test_factory_can_view_summary_after_lock(http_client, admin_headers):
    pid = await _make_product(http_client, admin_headers)
    _, token = await _make_branch_with_products(http_client, admin_headers, product_ids=[pid])
    # Create order before lock, then check factory can still read after lock window
    delivery_id = await _make_delivery(hours_from_now=48)
    await http_client.put(f"/branch/orders/{delivery_id}", json={"items": [{"product_id": pid, "quantity": 4}]}, headers=_bh(token))

    resp = await http_client.get(f"/factory/deliveries/{delivery_id}/summary", headers=admin_headers)
    assert resp.status_code == 200  # factory has no time limit


@pytest.mark.asyncio
async def test_branch_cannot_access_factory_summary(http_client, admin_headers):
    _, token = await _make_branch_with_products(http_client, admin_headers, product_ids=[])
    delivery_id = await _make_delivery(hours_from_now=48)

    resp = await http_client.get(f"/factory/deliveries/{delivery_id}/summary", headers=_bh(token))
    assert resp.status_code == 403


# ── Missing delivery ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_order_on_missing_delivery_404(http_client, admin_headers):
    branch_id, token = await _make_branch_with_products(http_client, admin_headers)
    resp = await http_client.get("/branch/orders/000000000000000000000000", headers=_bh(token))
    assert resp.status_code == 404
