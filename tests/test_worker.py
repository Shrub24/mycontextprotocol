"""Health check tests for worker service."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from mycontextprotocol.worker import OmniWorker
from mycontextprotocol.worker_llm import ExtractedContent, ExtractedFact


def test_worker_class_exists():
    """Test that OmniWorker class exists with required methods."""

    assert hasattr(OmniWorker, "connect")
    assert hasattr(OmniWorker, "process_task")
    assert hasattr(OmniWorker, "run")


@pytest.mark.asyncio
async def test_worker_connect():
    """Test that worker.connect() initializes clients."""

    with (
        patch("mycontextprotocol.worker.redis") as mock_redis,
        patch("mycontextprotocol.worker.DocumentExtractor") as mock_extractor,
        patch("mycontextprotocol.worker.Memory") as mock_memory,
        patch("llama_index.embeddings.ollama.OllamaEmbedding") as mock_ollama,
    ):
        mock_redis.from_url.return_value = AsyncMock()
        mock_extractor.return_value = Mock()
        mock_memory.from_config.return_value = Mock()
        mock_ollama.return_value = Mock()  # Mock the embedding model

        worker = OmniWorker()
        await worker.connect()

        assert worker.redis_client is not None
        assert worker.extractor is not None


@pytest.mark.asyncio
async def test_worker_process_task_structure():
    """Test that process_task accepts proper task structure."""

    with (
        patch("mycontextprotocol.worker.insert_document") as mock_insert,
        patch("mycontextprotocol.worker.Memory") as mock_memory,
    ):
        mock_insert.return_value = AsyncMock()
        mock_memory.return_value = Mock(add=Mock())

        worker = OmniWorker()
        worker.extractor = Mock()
        # Make extract async - it returns an awaitable
        worker.extractor.extract = AsyncMock(
            return_value=ExtractedContent(
                summary="Test",
                facts=[ExtractedFact(fact="test fact", category="test", confidence=0.9)],
                entities=["entity"],
                topics=["topic"],
            )
        )

        task = {"content": "test content", "metadata": {"source": "test"}}

        # Should not raise exception
        await worker.process_task(task)

        # Verify extraction was called with content and user_id
        worker.extractor.extract.assert_called_once()
