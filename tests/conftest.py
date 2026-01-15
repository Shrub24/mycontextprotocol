"""Pytest configuration and fixtures."""

import os

import pytest

from mycontextprotocol.config import Settings

# Set environment variables before settings usage
os.environ.update(
    {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "test",
        "POSTGRES_PASSWORD": "test",
        "POSTGRES_DB": "test",
        "DRAGONFLY_HOST": "localhost",
        "DRAGONFLY_PORT": "6379",
        "OLLAMA_BASE_URL": "http://localhost:11434",
        "OLLAMA_MODEL": "llama3.2",
        "LIGHTRAG_API_URL": "http://localhost:8000",
        "LIGHTRAG_API_KEY": "test-key",
        # LlamaIndex settings with LLAMAINDEX_ prefix
        "LLAMAINDEX_POSTGRES_HOST": "localhost",
        "LLAMAINDEX_POSTGRES_PORT": "5432",
        "LLAMAINDEX_POSTGRES_DATABASE": "test",
        "LLAMAINDEX_POSTGRES_USER": "test",
        "LLAMAINDEX_POSTGRES_PASSWORD": "test",
        "LLAMAINDEX_OLLAMA_BASE_URL": "http://localhost:11434",
        "LLAMAINDEX_OLLAMA_MODEL": "llama3.2",
    }
)


@pytest.fixture
def mock_settings():
    """Provide mock settings for tests."""
    return Settings.model_validate(
        {
            "postgres_host": "localhost",
            "postgres_port": 5432,
            "postgres_db": "test",
            "postgres_user": "test",
            "postgres_password": "test",
            "dragonfly_host": "localhost",
            "dragonfly_port": 6379,
            "ollama_base_url": "http://localhost:11434",
            "ollama_model": "llama3.2",
            "lightrag_api_url": "http://localhost:8000",
            "lightrag_api_key": "test-key",
        }
    )
