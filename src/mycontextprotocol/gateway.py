"""FastAPI Gateway for mycontextprotocol.

Provides REST API endpoints for:
- /context/state - Mem0 state injection (middleware pattern)
- /context/query/documents - LlamaIndex semantic search
- /context/query/graph - LightRAG graph queries
- /ingest - Document ingestion to memory stores
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Literal

app = FastAPI(
    title="mycontextprotocol",
    description="Memory-as-a-Service backend",
    version="0.1.0",
)


# Request/Response Models
class StateRequest(BaseModel):
    user_id: str
    session_id: str | None = None


class StateResponse(BaseModel):
    user_id: str
    memories: list[dict]
    context: str


class DocumentQueryRequest(BaseModel):
    query: str
    limit: int = 10


class DocumentQueryResponse(BaseModel):
    results: list[dict]
    query_time_ms: float
    store: Literal["llamaindex"] = "llamaindex"


class GraphQueryRequest(BaseModel):
    query: str
    mode: Literal["local", "global", "hybrid", "naive"] = "hybrid"
    limit: int = 10


class GraphQueryResponse(BaseModel):
    results: list[dict]
    query_time_ms: float
    store: Literal["lightrag"] = "lightrag"
    mode_used: str


class IngestRequest(BaseModel):
    content: str
    metadata: dict | None = None
    stores: list[Literal["llamaindex", "lightrag"]] = ["llamaindex", "lightrag"]


class IngestResponse(BaseModel):
    status: str
    document_id: str
    stores_updated: list[str]


# Health check
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


# Tier 1: STATE (Mem0) - Middleware pattern
@app.post("/context/state", response_model=StateResponse)
async def get_state(request: StateRequest):
    """Get user state/preferences from Mem0.

    Called automatically by OpenWebUI middleware on most requests.
    Returns subjective user facts for context injection.
    """
    # TODO: Integrate Mem0 client
    raise HTTPException(status_code=501, detail="Mem0 integration pending")


# Tier 2: LONG (LlamaIndex) - Explicit tool
@app.post("/context/query/documents", response_model=DocumentQueryResponse)
async def query_documents(request: DocumentQueryRequest):
    """Search documents using LlamaIndex semantic search.

    Agent explicitly calls this when it needs document content.
    """
    # TODO: Integrate LlamaIndex PGVectorStore
    raise HTTPException(status_code=501, detail="LlamaIndex integration pending")


# Tier 3: RELATIONAL (LightRAG) - Explicit tool
@app.post("/context/query/graph", response_model=GraphQueryResponse)
async def query_graph(request: GraphQueryRequest):
    """Query knowledge graph using LightRAG.

    Agent explicitly calls this when it needs entity relationships.
    """
    # TODO: Integrate LightRAG client
    raise HTTPException(status_code=501, detail="LightRAG integration pending")


# Ingestion endpoint
@app.post("/ingest", response_model=IngestResponse)
async def ingest(request: IngestRequest):
    """Ingest content into memory stores.

    Queues document for processing by Omni-Worker.
    """
    # TODO: Queue to Dragonfly for worker processing
    raise HTTPException(status_code=501, detail="Ingestion queue pending")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
