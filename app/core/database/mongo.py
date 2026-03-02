"""MongoDB async client via Motor.

Provides a thin wrapper around ``motor.motor_asyncio`` so that the
connection lifecycle is managed in ``lifespan.py``.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings


def create_mongo_client() -> AsyncIOMotorClient:  # type: ignore[type-arg]
    """Create an async MongoDB client."""
    return AsyncIOMotorClient(settings.MONGO_URL)


def get_mongo_database(client: AsyncIOMotorClient) -> AsyncIOMotorDatabase:  # type: ignore[type-arg]
    """Return the default database handle from *client*."""
    return client[settings.MONGO_DB]
