# Architecture

**Analysis Date:** 2026-01-15

## Pattern Overview

**Overall:** FastAPI gateway + async worker with queue-driven ingestion

**Key Characteristics:**
- Queue-based ingestion via Dragonfly (Redis-compatible)
- Three-tier memory (Mem0, LlamaIndex, LightRAG)
- Kubernetes deployment via Helmfile

## Layers

**API Layer:**
- Purpose: HTTP endpoints for state/query/ingest
- Contains: FastAPI app and request models (`src/mycontextprotocol/gateway.py`)
- Depends on: memory clients + Redis queue

**Ingestion Layer:**
- Purpose: Queue management and async processing
- Contains: Dragonfly queue usage (`src/mycontextprotocol/gateway.py`, `src/mycontextprotocol/worker.py`)
- Depends on: Redis/Dragonfly and worker extraction

**Processing Layer:**
- Purpose: LLM extraction + writes to memory stores
- Contains: OmniWorker + DocumentExtractor (`src/mycontextprotocol/worker.py`, `src/mycontextprotocol/worker_llm.py`)
- Depends on: Mem0, LlamaIndex, LightRAG clients

**Storage/Query Layer:**
- Purpose: Long-term memory and retrieval
- Contains: Mem0 + LlamaIndex + LightRAG clients (`src/mycontextprotocol/memory/*`)
- Depends on: Postgres + LightRAG service

## Data Flow

**Ingestion Flow:**
1. Client POST `/ingest` (`src/mycontextprotocol/gateway.py`)
2. Gateway enqueues message in Dragonfly list
3. Worker consumes queue (`src/mycontextprotocol/worker.py`)
4. DocumentExtractor produces summary/facts (`src/mycontextprotocol/worker_llm.py`)
5. Writes to Mem0, LlamaIndex, LightRAG (`src/mycontextprotocol/memory/*`)

**Query Flow (State):**
1. Client POST `/context/state`
2. Gateway queries Mem0 for user state
3. Response includes formatted context string

**Query Flow (Tools):**
1. Client POST `/context/query/documents` → LlamaIndex
2. Client POST `/context/query/graph` → LightRAG

**State Management:**
- Stateless services; state persists in Postgres and LightRAG

## Key Abstractions

**Settings:**
- Purpose: Centralized configuration
- Examples: `src/mycontextprotocol/config.py`, `src/mycontextprotocol/memory/*_client.py`

**DocumentExtractor:**
- Purpose: LLM extraction into structured data
- Example: `src/mycontextprotocol/worker_llm.py`

**Memory Clients:**
- Purpose: Abstract external stores
- Examples: `src/mycontextprotocol/memory/mem0_client.py`, `src/mycontextprotocol/memory/llamaindex_store.py`, `src/mycontextprotocol/memory/lightrag_client.py`

## Entry Points

**Gateway:**
- Location: `src/mycontextprotocol/gateway.py`
- Triggers: HTTP requests
- Responsibilities: Validate requests, route to memory clients, enqueue ingestion

**Worker:**
- Location: `src/mycontextprotocol/worker.py`
- Triggers: Dragonfly queue messages
- Responsibilities: Extract content, write to memory stores

## Error Handling

**Strategy:**
- FastAPI raises HTTP errors per request
- Worker logs errors and pushes to dead-letter queue

**Patterns:**
- Health endpoints return 503 on dependency failures (`src/mycontextprotocol/health.py`)

## Cross-Cutting Concerns

**Logging:**
- Python logging used in gateway and worker (`src/mycontextprotocol/gateway.py`, `src/mycontextprotocol/worker.py`)

**Validation:**
- Pydantic request/response models (`src/mycontextprotocol/gateway.py`)

**Configuration:**
- Environment-based settings (`src/mycontextprotocol/config.py`)

---

*Architecture analysis: 2026-01-15*
*Update when major patterns change*
