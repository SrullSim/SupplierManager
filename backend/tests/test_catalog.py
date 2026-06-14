"""Catalog (product) endpoint tests, including authorization checks."""

import pytest


@pytest.mark.asyncio
async def test_create_product(http_client, admin_headers):
    resp = await http_client.post("/factory/products", json={"name": "challah", "unit": "loaf"}, headers=admin_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "challah"
    assert data["unit"] == "loaf"
    assert data["active"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_list_products(http_client, admin_headers):
    await http_client.post("/factory/products", json={"name": "challah", "unit": "loaf"}, headers=admin_headers)
    await http_client.post("/factory/products", json={"name": "borekas", "unit": "tray"}, headers=admin_headers)
    resp = await http_client.get("/factory/products", headers=admin_headers)
    assert resp.status_code == 200
    names = {p["name"] for p in resp.json()}
    assert names == {"challah", "borekas"}


@pytest.mark.asyncio
async def test_update_product(http_client, admin_headers):
    create = await http_client.post(
        "/factory/products", json={"name": "challah", "unit": "loaf"}, headers=admin_headers
    )
    product_id = create.json()["id"]

    resp = await http_client.patch(f"/factory/products/{product_id}", json={"active": False}, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["active"] is False


@pytest.mark.asyncio
async def test_update_missing_product(http_client, admin_headers):
    resp = await http_client.patch(
        "/factory/products/000000000000000000000000", json={"name": "x"}, headers=admin_headers
    )
    assert resp.status_code == 404


# ── Authorization ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_product_requires_auth(http_client):
    resp = await http_client.post("/factory/products", json={"name": "challah", "unit": "loaf"})
    assert resp.status_code == 401  # no bearer token at all → unauthenticated


@pytest.mark.asyncio
async def test_branch_user_cannot_create_product(http_client, branch_user):
    login = await http_client.post("/auth/login", json={"branch_code": "branch01", "password": "branch1234"})
    token = login.json()["access_token"]
    resp = await http_client.post(
        "/factory/products",
        json={"name": "challah", "unit": "loaf"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403  # branch_user lacks factory_admin role


# ── Validation ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_product_rejects_empty_name(http_client, admin_headers):
    resp = await http_client.post("/factory/products", json={"name": "", "unit": "loaf"}, headers=admin_headers)
    assert resp.status_code == 422
