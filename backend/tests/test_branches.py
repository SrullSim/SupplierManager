"""Branch management tests: creation + credentials, assignment, least-privilege isolation."""

import pytest

from auth.models import User


async def _create_product(http_client, headers, name="challah", unit="loaf") -> str:
    resp = await http_client.post("/factory/products", json={"name": name, "unit": unit}, headers=headers)
    return resp.json()["id"]


# ── Creation + credentials ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_branch_issues_credentials(http_client, admin_headers):
    resp = await http_client.post(
        "/factory/branches", json={"branch_code": "jeru01", "name": "Jerusalem Center"}, headers=admin_headers
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["branch_code"] == "jeru01"
    assert data["generated_password"]  # password returned once

    # A branch_user login identity must now exist.
    user = await User.find_one(User.branch_code == "jeru01")
    assert user is not None
    assert user.role == "branch_user"
    assert user.branch_id == data["id"]


@pytest.mark.asyncio
async def test_created_branch_can_log_in(http_client, admin_headers):
    create = await http_client.post(
        "/factory/branches", json={"branch_code": "jeru01", "name": "Jerusalem"}, headers=admin_headers
    )
    password = create.json()["generated_password"]

    login = await http_client.post("/auth/login", json={"branch_code": "jeru01", "password": password})
    assert login.status_code == 200
    assert "access_token" in login.json()


@pytest.mark.asyncio
async def test_duplicate_branch_code_rejected(http_client, admin_headers):
    await http_client.post("/factory/branches", json={"branch_code": "jeru01", "name": "A"}, headers=admin_headers)
    resp = await http_client.post(
        "/factory/branches", json={"branch_code": "jeru01", "name": "B"}, headers=admin_headers
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_branch_code_collides_with_admin(http_client, admin_headers):
    # "admin" is the factory_admin's branch_code from the fixture.
    resp = await http_client.post(
        "/factory/branches", json={"branch_code": "admin", "name": "X"}, headers=admin_headers
    )
    assert resp.status_code == 409


# ── Product assignment ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_assign_products(http_client, admin_headers):
    pid = await _create_product(http_client, admin_headers)
    branch = await http_client.post(
        "/factory/branches", json={"branch_code": "jeru01", "name": "J"}, headers=admin_headers
    )
    branch_id = branch.json()["id"]

    resp = await http_client.put(
        f"/factory/branches/{branch_id}/products", json={"product_ids": [pid]}, headers=admin_headers
    )
    assert resp.status_code == 200
    assert resp.json()["assigned_product_ids"] == [pid]


@pytest.mark.asyncio
async def test_assign_invalid_product_rejected(http_client, admin_headers):
    branch = await http_client.post(
        "/factory/branches", json={"branch_code": "jeru01", "name": "J"}, headers=admin_headers
    )
    branch_id = branch.json()["id"]
    resp = await http_client.put(
        f"/factory/branches/{branch_id}/products",
        json={"product_ids": ["000000000000000000000000"]},
        headers=admin_headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_assign_dedupes(http_client, admin_headers):
    pid = await _create_product(http_client, admin_headers)
    branch = await http_client.post(
        "/factory/branches", json={"branch_code": "jeru01", "name": "J"}, headers=admin_headers
    )
    branch_id = branch.json()["id"]
    resp = await http_client.put(
        f"/factory/branches/{branch_id}/products", json={"product_ids": [pid, pid]}, headers=admin_headers
    )
    assert resp.json()["assigned_product_ids"] == [pid]


# ── Least-privilege isolation (security requirement) ───────────────────────────


@pytest.mark.asyncio
async def test_branch_sees_only_assigned_products(http_client, admin_headers):
    p_assigned = await _create_product(http_client, admin_headers, "challah", "loaf")
    await _create_product(http_client, admin_headers, "secret-cake", "unit")  # NOT assigned

    branch = await http_client.post(
        "/factory/branches", json={"branch_code": "jeru01", "name": "J"}, headers=admin_headers
    )
    branch_id = branch.json()["id"]
    password = branch.json()["generated_password"]

    await http_client.put(
        f"/factory/branches/{branch_id}/products", json={"product_ids": [p_assigned]}, headers=admin_headers
    )

    login = await http_client.post("/auth/login", json={"branch_code": "jeru01", "password": password})
    branch_token = login.json()["access_token"]

    resp = await http_client.get("/branch/products", headers={"Authorization": f"Bearer {branch_token}"})
    assert resp.status_code == 200
    names = {p["name"] for p in resp.json()}
    assert names == {"challah"}  # the unassigned product is invisible


@pytest.mark.asyncio
async def test_branch_does_not_see_inactive_assigned_product(http_client, admin_headers):
    pid = await _create_product(http_client, admin_headers, "challah", "loaf")
    branch = await http_client.post(
        "/factory/branches", json={"branch_code": "jeru01", "name": "J"}, headers=admin_headers
    )
    branch_id = branch.json()["id"]
    password = branch.json()["generated_password"]
    await http_client.put(f"/factory/branches/{branch_id}/products", json={"product_ids": [pid]}, headers=admin_headers)
    # Deactivate the product
    await http_client.patch(f"/factory/products/{pid}", json={"active": False}, headers=admin_headers)

    login = await http_client.post("/auth/login", json={"branch_code": "jeru01", "password": password})
    branch_token = login.json()["access_token"]
    resp = await http_client.get("/branch/products", headers={"Authorization": f"Bearer {branch_token}"})
    assert resp.json() == []  # inactive product hidden


@pytest.mark.asyncio
async def test_branch_cannot_list_all_branches(http_client, branch_user):
    login = await http_client.post("/auth/login", json={"branch_code": "branch01", "password": "branch1234"})
    token = login.json()["access_token"]
    resp = await http_client.get("/factory/branches", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
