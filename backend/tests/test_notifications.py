"""Push-token registration: multiple devices per branch, idempotency, no-op send."""

import pytest

from notifications import service as notifications
from notifications.models import PushToken


async def _branch_token(http_client, admin_headers, code="push01") -> tuple[str, str]:
    resp = await http_client.post(
        "/factory/branches", json={"branch_code": code, "name": f"Branch {code}"}, headers=admin_headers
    )
    branch_id = resp.json()["id"]
    password = resp.json()["generated_password"]
    login = await http_client.post("/auth/login", json={"branch_code": code, "password": password})
    return branch_id, login.json()["access_token"]


@pytest.mark.asyncio
async def test_register_push_token(http_client, admin_headers):
    _, token = await _branch_token(http_client, admin_headers)
    resp = await http_client.post(
        "/branch/push-token",
        json={"token": "fcm-aaa", "device_label": "Pixel"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["device_label"] == "Pixel"


@pytest.mark.asyncio
async def test_multiple_tokens_per_branch(http_client, admin_headers):
    branch_id, token = await _branch_token(http_client, admin_headers)
    headers = {"Authorization": f"Bearer {token}"}
    await http_client.post("/branch/push-token", json={"token": "dev-1"}, headers=headers)
    await http_client.post("/branch/push-token", json={"token": "dev-2"}, headers=headers)

    tokens = await notifications.tokens_for_branch(branch_id)
    assert set(tokens) == {"dev-1", "dev-2"}


@pytest.mark.asyncio
async def test_register_same_token_idempotent(http_client, admin_headers):
    branch_id, token = await _branch_token(http_client, admin_headers)
    headers = {"Authorization": f"Bearer {token}"}
    await http_client.post("/branch/push-token", json={"token": "dup", "device_label": "old"}, headers=headers)
    await http_client.post("/branch/push-token", json={"token": "dup", "device_label": "new"}, headers=headers)

    docs = await PushToken.find(PushToken.branch_id == branch_id).to_list()
    assert len(docs) == 1
    assert docs[0].device_label == "new"  # re-register refreshes the label


@pytest.mark.asyncio
async def test_send_to_branch_noop_counts_tokens(http_client, admin_headers):
    branch_id, token = await _branch_token(http_client, admin_headers)
    headers = {"Authorization": f"Bearer {token}"}
    await http_client.post("/branch/push-token", json={"token": "t1"}, headers=headers)
    await http_client.post("/branch/push-token", json={"token": "t2"}, headers=headers)

    # No Firebase creds in tests → no-op sender returns the token count.
    sent = await notifications.send_to_branch(branch_id, "title", "body")
    assert sent == 2


@pytest.mark.asyncio
async def test_send_to_branch_no_tokens(http_client, admin_headers):
    branch_id, _ = await _branch_token(http_client, admin_headers)
    sent = await notifications.send_to_branch(branch_id, "title", "body")
    assert sent == 0


@pytest.mark.asyncio
async def test_factory_cannot_register_push_token(http_client, admin_headers):
    resp = await http_client.post("/branch/push-token", json={"token": "x"}, headers=admin_headers)
    assert resp.status_code == 403  # factory admin is not a branch user
