"""LlamaIndex store for Tier 2 (LONG) memory.

Manages full documents with semantic search.
Uses PostgreSQL + pgvector backend.
"""

from typing import Any

from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.vector_stores.postgres import PGVectorStore
from pydantic_settings import BaseSettings


class LlamaIndexSettings(BaseSettings):
    """LlamaIndex configuration from environment."""

    postgres_host: str = "postgresql-cluster-rw.database.svc.cluster.local"
    postgres_port: str = "5432"
    postgres_database: str = "llamaindex"
    postgres_user: str = "app"
    postgres_password: str
    openai_api_key: str

    model_config = {"env_prefix": "LLAMAINDEX_"}


def create_llamaindex_store() -> PGVectorStore:
    """Create configured LlamaIndex PGVectorStore instance.

    Returns:
        PGVectorStore connected to PostgreSQL backend
    """
    settings = LlamaIndexSettings.model_validate({})

    return PGVectorStore.from_params(
        host=settings.postgres_host,
        port=settings.postgres_port,
        database=settings.postgres_database,
        user=settings.postgres_user,
        password=settings.postgres_password,
        table_name="llamaindex_vectors",
        embed_dim=768,
        hybrid_search=True,
        text_search_config="english",
        hnsw_kwargs={
            "hnsw_m": 16,
            "hnsw_ef_construction": 64,
            "hnsw_ef_search": 40,
            "hnsw_dist_method": "vector_cosine_ops",
        },
    )


def create_index() -> VectorStoreIndex:
    """Create VectorStoreIndex with PGVectorStore backend.

    Returns:
        VectorStoreIndex for querying documents
    """
    vector_store = create_llamaindex_store()
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    return VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        storage_context=storage_context,
    )


async def query_documents(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Query documents using semantic search.

    Args:
        query: Search query
        limit: Maximum results to return

    Returns:
        List of matching documents with scores
    """
    index = create_index()

    query_engine = index.as_query_engine(
        similarity_top_k=limit,
    )

    response = query_engine.query(query)

    results = []
    for node in response.source_nodes:
        results.append(
            {
                "id": node.node_id,
                "content": node.text,
                "score": node.score,
                "metadata": node.metadata,
            }
        )

    return results
