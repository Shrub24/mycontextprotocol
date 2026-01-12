"""FastAPI Gateway for mycontextprotocol.

Provides REST API endpoints for:
- /context/state - Mem0 state injection (middleware pattern)
- /context/query/documents - LlamaIndex semantic search
- /context/query/graph - LightRAG graph queries
- /ingest - Document ingestion to memory stores
"""

from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from mycontextprotocol.config import Settings
from mycontextprotocol.health import (
    HealthResponse,
    aggregate_health_status,
    check_dragonfly,
    check_postgres,
)

settings = Settings.model_validate({})

app = FastAPI(
    title="mycontextprotocol",
    description="Memory-as-a-Service backend",
    version="0.1.0",
)


class StateRequest(BaseModel):
    """Request user state from Mem0."""

    user_id: str = Field(..., description="User identifier for memory lookup")
    session_id: str | None = Field(
        None, description="Optional session identifier for context scoping"
    )


class StateResponse(BaseModel):
    """User state from Mem0 with formatted context."""

    user_id: str = Field(..., description="User identifier")
    memories: list[dict[str, Any]] = Field(..., description="Raw memory objects from Mem0")
    context: str = Field(..., description="Formatted context string for LLM injection")


class DocumentQueryRequest(BaseModel):
    """Semantic search query for LlamaIndex document store."""

    query: str = Field(..., description="Natural language search query")
    limit: int = Field(10, description="Maximum number of results to return", ge=1, le=100)


class DocumentQueryResponse(BaseModel):
    """Results from LlamaIndex semantic search."""

    results: list[dict[str, Any]] = Field(
        ..., description="Matching documents with scores and metadata"
    )
    query_time_ms: float = Field(..., description="Query execution time in milliseconds")
    store: Literal["llamaindex"] = Field("llamaindex", description="Source store identifier")


class GraphQueryRequest(BaseModel):
    """Knowledge graph query for LightRAG."""

    query: str = Field(..., description="Natural language query for graph traversal")
    mode: Literal["local", "global", "hybrid", "naive"] = Field(
        "hybrid",
        description="Query mode: local (entity-focused), global (relationship-focused), hybrid (combined), naive (keyword)",
    )
    limit: int = Field(10, description="Maximum number of results to return", ge=1, le=100)


class GraphQueryResponse(BaseModel):
    """Results from LightRAG graph query."""

    results: list[dict[str, Any]] = Field(
        ..., description="Graph query results with entities and relationships"
    )
    query_time_ms: float = Field(..., description="Query execution time in milliseconds")
    store: Literal["lightrag"] = Field("lightrag", description="Source store identifier")
    mode_used: str = Field(..., description="Query mode that was executed")


class IngestRequest(BaseModel):
    """Request to ingest content into memory stores."""

    content: str = Field(..., description="Document content to ingest")
    metadata: dict[str, Any] | None = Field(
        None, description="Optional metadata tags for the document"
    )
    stores: list[Literal["llamaindex", "lightrag"]] = Field(
        ["llamaindex", "lightrag"], description="Target stores for ingestion (default: both)"
    )


class IngestResponse(BaseModel):
    """Result of content ingestion."""

    status: str = Field(..., description="Ingestion status: queued, processing, completed, failed")
    document_id: str = Field(..., description="Unique identifier for the ingested document")
    stores_updated: list[str] = Field(..., description="Stores that received the content")


@app.get("/livez")
async def liveness():
    return Response(status_code=200)


@app.get("/readyz")
async def readiness() -> JSONResponse:
    checks = {}

    postgres_check = await check_postgres(
        connection_string=settings.postgres_connection_string, timeout=5.0
    )
    checks["postgres"] = postgres_check

    dragonfly_check = await check_dragonfly(
        host=settings.dragonfly_host, port=settings.dragonfly_port, timeout=5.0
    )
    checks["dragonfly"] = dragonfly_check

    overall_status = aggregate_health_status(checks)

    if overall_status == "fail":
        return JSONResponse(
            status_code=503,
            content={
                "status": overall_status,
                "checks": {k: v.model_dump() for k, v in checks.items()},
            },
        )

    return JSONResponse(
        status_code=200,
        content={
            "status": overall_status,
            "checks": {k: v.model_dump() for k, v in checks.items()},
        },
    )


@app.get("/health", response_model=HealthResponse)
async def health():
    checks = {}

    postgres_check = await check_postgres(
        connection_string=settings.postgres_connection_string, timeout=5.0
    )
    checks["postgres"] = postgres_check

    dragonfly_check = await check_dragonfly(
        host=settings.dragonfly_host, port=settings.dragonfly_port, timeout=5.0
    )
    checks["dragonfly"] = dragonfly_check

    overall_status = aggregate_health_status(checks)

    return HealthResponse(status=overall_status, version="0.1.0", checks=checks)


# Tier 1: STATE (Mem0) - Middleware pattern
@app.post("/context/state", response_model=StateResponse)
async def get_state(_request: StateRequest):
    """Get user state/preferences from Mem0.

    Called automatically by OpenWebUI middleware on most requests.
    Returns subjective user facts for context injection.
    """
    raise HTTPException(status_code=501, detail="Mem0 integration pending")


# Tier 2: LONG (LlamaIndex) - Explicit tool
@app.post("/context/query/documents", response_model=DocumentQueryResponse)
async def query_documents(_request: DocumentQueryRequest):
    """Search documents using LlamaIndex semantic search.

    Agent explicitly calls this when it needs document content.
    """
    raise HTTPException(status_code=501, detail="LlamaIndex integration pending")


# Tier 3: RELATIONAL (LightRAG) - Explicit tool
@app.post("/context/query/graph", response_model=GraphQueryResponse)
async def query_graph(_request: GraphQueryRequest):
    """Query knowledge graph using LightRAG.

    Agent explicitly calls this when it needs entity relationships.
    """
    raise HTTPException(status_code=501, detail="LightRAG integration pending")


# Ingestion endpoint
@app.post("/ingest", response_model=IngestResponse)
async def ingest(_request: IngestRequest):
    """Ingest content into memory stores.

    Queues document for processing by Omni-Worker.
    """
    raise HTTPException(status_code=501, detail="Ingestion queue pending")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
