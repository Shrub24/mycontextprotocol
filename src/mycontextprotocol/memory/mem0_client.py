"""Mem0 client for Tier 1 (STATE) memory.

Manages subjective user facts and preferences.
Uses CloudNativePG as backend store.
"""

from typing import Any

from mem0 import Memory
from pydantic_settings import BaseSettings


class Mem0Settings(BaseSettings):
    """Mem0 configuration from environment."""

    postgres_host: str = "postgresql-cluster-rw.database.svc.cluster.local"
    postgres_port: int = 5432
    postgres_database: str = "mem0"
    postgres_user: str = "app"
    postgres_password: str = ""

    model_config = {"env_prefix": "MEM0_"}


def create_mem0_client() -> Memory:
    """Create configured Mem0 client instance.

    Returns:
        Memory client connected to PostgreSQL backend
    """
    settings = Mem0Settings.model_validate({})

    config = {
        "vector_store": {
            "provider": "pgvector",
            "config": {
                "host": settings.postgres_host,
                "port": settings.postgres_port,
                "dbname": settings.postgres_database,
                "user": settings.postgres_user,
                "password": settings.postgres_password,
                "collection_name": "mem0",
                "embedding_model_dims": 768,
            },
        }
    }

    return Memory.from_config(config)


def get_mem0_config() -> dict[str, Any]:
    """Get Mem0 configuration dict.

    Returns:
        Dict with vector_store config for PostgreSQL + pgvector
    """
    settings = Mem0Settings.model_validate({})

    return {
        "vector_store": {
            "provider": "pgvector",
            "config": {
                "dbname": settings.postgres_database,
                "user": settings.postgres_user,
                "password": settings.postgres_password,
                "host": settings.postgres_host,
                "port": settings.postgres_port,
                "collection_name": "mem0",
                "embedding_model_dims": 768,
            },
        },
    }


async def get_user_state(user_id: str, _session_id: str | None = None) -> dict[str, Any]:
    """Get user state from Mem0.

    Args:
        user_id: User identifier
        _session_id: Optional session identifier (unused, reserved for future use)

    Returns:
        Dict with memories and formatted context string
    """
    client = create_mem0_client()

    memories = client.search(
        query="",
        user_id=user_id,
        limit=50,
    )

    context_parts = []
    for memory in memories:
        if isinstance(memory, dict):
            memory_text = memory.get("memory", "")
            if memory_text:
                context_parts.append(f"- {memory_text}")

    context = "\n".join(context_parts) if context_parts else "No user context available."

    return {
        "user_id": user_id,
        "memories": memories,
        "context": context,
    }
