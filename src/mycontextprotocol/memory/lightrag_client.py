"""LightRAG client for Tier 3 (RELATIONAL) memory.

Manages knowledge graph queries via LightRAG REST API.
Calls external LightRAG service deployed in k8s cluster.
"""

from typing import Any, Literal

import httpx
from pydantic_settings import BaseSettings


class LightRAGSettings(BaseSettings):
    """LightRAG configuration from environment."""

    lightrag_host: str = "lightrag.lightrag.svc.cluster.local"
    lightrag_port: int = 9621
    lightrag_api_key: str = ""

    model_config = {"env_prefix": "LIGHTRAG_"}

    @property
    def base_url(self) -> str:
        return f"http://{self.lightrag_host}:{self.lightrag_port}"


_http_client: httpx.AsyncClient | None = None


def get_http_client() -> httpx.AsyncClient:
    """Get or create shared HTTP client with connection pooling."""
    global _http_client  # noqa: PLW0603
    if _http_client is None:
        settings = LightRAGSettings.model_validate({})
        headers = {}
        if settings.lightrag_api_key:
            headers["X-API-Key"] = settings.lightrag_api_key

        _http_client = httpx.AsyncClient(
            base_url=settings.base_url,
            headers=headers,
            timeout=30.0,
        )
    return _http_client


async def query_graph(
    query: str,
    mode: Literal["local", "global", "hybrid", "naive"] = "hybrid",
    limit: int = 10,
) -> dict[str, Any]:
    """Query LightRAG knowledge graph.

    Args:
        query: Natural language query
        mode: Query mode (local=entity-focused, global=relationship-focused, hybrid=both, naive=keyword)
        limit: Maximum results to return

    Returns:
        Dict with 'results' list and metadata
    """
    client = get_http_client()

    payload = {
        "query": query,
        "mode": mode,
        "top_k": limit,
        "only_need_context": False,
    }

    response = await client.post("/query", json=payload)
    response.raise_for_status()

    data = response.json()

    results = []
    if "references" in data:
        for ref in data["references"]:
            results.append(
                {
                    "content": ref.get("content", ""),
                    "source": ref.get("source", ""),
                    "score": ref.get("score", 0.0),
                }
            )

    return {
        "results": results,
        "response": data.get("response", ""),
    }


async def insert_document(text: str, metadata: dict[str, Any] | None = None) -> str:
    """Insert document into LightRAG for graph extraction.

    Args:
        text: Document content
        metadata: Optional metadata (used for file_source field)

    Returns:
        Track ID for monitoring ingestion status
    """
    client = get_http_client()

    payload = {
        "text": text,
        "file_source": metadata.get("source", "api") if metadata else "api",
    }

    response = await client.post("/documents/text", json=payload)
    response.raise_for_status()

    data = response.json()
    return data.get("track_id", "")


async def close_client() -> None:
    """Close HTTP client connection pool."""
    global _http_client  # noqa: PLW0603
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None
