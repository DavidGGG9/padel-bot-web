import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from pymongo import AsyncMongoClient
from pymongo.server_api import ServerApi

logger = logging.getLogger(__name__)


@asynccontextmanager
async def instantiate_mongodb_client(
    user: str,
    password: str,
) -> AsyncGenerator[AsyncMongoClient[dict[str, Any]]]:
    """Async context manager to create and manage a MongoDB client connection."""
    uri = f"mongodb+srv://{user}:{password}@cluster0.dkiat2v.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    client: AsyncMongoClient[dict[str, Any]] = AsyncMongoClient(uri, server_api=ServerApi("1"))

    try:
        await client.admin.command("ping")
        logger.info("Connection to MongoDB successful!")
        yield client

    except Exception:
        logger.exception("MongoDB connection failed")
        raise
    finally:
        await client.close()
        logger.info("Connection to MongoDB successfully closed!")


async def test_mongodb_connection(user: str, password: str) -> bool:
    """Utility function to test the connection to MongoDB with the provided credentials."""
    uri = f"mongodb+srv://{user}:{password}@cluster0.dkiat2v.mongodb.net/"
    client: AsyncMongoClient[dict[str, Any]] = AsyncMongoClient(uri, server_api=ServerApi("1"))

    try:
        await client.admin.command("ping")
    except Exception:
        logger.exception("❌ MongoDB test connection failed")
        return False
    else:
        logger.info("✅ MongoDB connection successful!")
        return True
    finally:
        await client.close()
