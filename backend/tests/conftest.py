import os

import pytest
import pytest_asyncio
from beanie import init_beanie
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient

os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-prod")
os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017")
os.environ.setdefault("MONGO_DB_NAME", "bakery_test")

from auth.models import RefreshToken, User  # noqa: E402
from branches.models import Branch  # noqa: E402
from catalog.models import Product  # noqa: E402
from deliveries.models import Delivery, DeliverySchedule  # noqa: E402
from main import app  # noqa: E402
from notifications.models import PushToken  # noqa: E402
from orders.models import Order  # noqa: E402


@pytest_asyncio.fixture(autouse=True)
async def init_test_db():
    client = AsyncMongoMockClient()
    await init_beanie(
        database=client["bakery_test"],
        document_models=[User, RefreshToken, Product, Branch, Delivery, DeliverySchedule, Order, PushToken],
    )
    yield
    # mongomock resets state between tests automatically


@pytest_asyncio.fixture
async def http_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def factory_admin(init_test_db) -> User:
    from core.security import hash_password

    user = User(role="factory_admin", branch_code="admin", hashed_password=hash_password("admin1234"))
    await user.insert()
    return user


@pytest_asyncio.fixture
async def branch_user(init_test_db) -> User:
    from core.security import hash_password

    user = User(
        role="branch_user",
        branch_code="branch01",
        hashed_password=hash_password("branch1234"),
        branch_id="branch-id-001",
    )
    await user.insert()
    return user


@pytest_asyncio.fixture
async def admin_headers(http_client, factory_admin) -> dict:
    resp = await http_client.post("/auth/login", json={"branch_code": "admin", "password": "admin1234"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
