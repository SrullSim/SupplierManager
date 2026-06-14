from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from core.config import settings

_client: AsyncIOMotorClient | None = None  # type: ignore[type-arg]


async def connect_db(document_models: list) -> None:  # type: ignore[type-arg]
    global _client
    _client = AsyncIOMotorClient(settings.mongo_uri)
    await init_beanie(database=_client[settings.mongo_db_name], document_models=document_models)


async def close_db() -> None:
    if _client:
        _client.close()
