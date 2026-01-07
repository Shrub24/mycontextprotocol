"""LlamaIndex store for Tier 2 (LONG) memory.

Manages full documents with semantic search.
Uses PostgreSQL + pgvector backend.
"""

from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.postgres import PGVectorStore
from pydantic_settings import BaseSettings


class LlamaIndexSettings(BaseSettings):
    """LlamaIndex configuration from environment."""

    postgres_host: str = "postgresql-cluster-rw.database.svc.cluster.local"
    postgres_port: int = 5432
    postgres_database: str = "llamaindex"
    postgres_user: str = "app"
    postgres_password: str

    openai_api_key: str

    model_config = {"env_prefix": "LLAMAINDEX_"}


def create_vector_store() -> PGVectorStore:
    """Create PGVectorStore instance.

    Returns:
        Configured PGVectorStore connected to PostgreSQL
    """
    settings = LlamaIndexSettings()

    return PGVectorStore.from_params(
        host=settings.postgres_host,
        port=settings.postgres_port,
        database=settings.postgres_database,
        user=settings.postgres_user,
        password=settings.postgres_password,
        table_name="llamaindex_vectors",
        embed_dim=1536,  # OpenAI ada-002
    )


def create_index() -> VectorStoreIndex:
    """Create VectorStoreIndex with PGVectorStore backend.

    Returns:
        VectorStoreIndex for querying documents
    """
    vector_store = create_vector_store()
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    return VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        storage_context=storage_context,
    )


async def query_documents(query: str, limit: int = 10) -> list[dict]:
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

    # Format results
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
