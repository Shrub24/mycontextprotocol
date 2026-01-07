# mycontextprotocol Architecture

## 1. Executive Summary

**mycontextprotocol** is a self-hosted personal memory and context management system designed as a "Memory-as-a-Service" backend. The system is architected in two distinct parts:

1. **MyContextProtocol (Part A)** - The backend product: a standalone, deployable memory API with intelligent processing
2. **Personal AI Stack (Part B)** - The frontend integration: user-facing tools (OpenWebUI, LiteLLM, etc.) that consume the memory API

The core philosophy is **Sovereign + Cloud-Agnostic + Hybrid Intelligence**: users own their infrastructure, can deploy anywhere, and benefit from both vector-based semantic search and AI-extracted knowledge graphs.

**Key Capabilities:**

- **Unified Memory Ingestion** - Capture information from multiple sources with intelligent extraction
- **Subjective/Objective Split** - Separate user preferences (Mem0) from factual knowledge (LlamaIndex)
- **State vs Tools Pattern** - Context automatically injected (State), knowledge retrieved on-demand (Tools)
- **Semantic Search** - Vector embeddings with pgvector for context-aware retrieval
- **Self-Hosted & Portable** - Run on any Linux VM (Oracle Cloud ARM, local k3d)
- **Cloud-Agnostic** - No vendor lock-in

---

## 2. The Two-Part Architecture

### 2.1 Part A: MyContextProtocol (The Backend Product)

**Definition**: A standalone, deployable "Memory-as-a-Service" API.

**Goal**: Reusable product with its own Helm Chart that multiple agents (Laptop, Cloud, Phone) can share.

**Components**:

- **API Gateway**: FastAPI/Go service exposing `/context/state` (middleware) and `/context/query` (tool) endpoints
- **Workers**: KEDA-scaled batch processors (Omni-Worker pattern)
- **State Layer**: CloudNativePG (Postgres) + Dragonfly (Queue + Cache)

**Why Separate?**: Allows multiple frontends (OpenWebUI, CLI, browser extension) to share a single "Brain" without tight coupling to any specific UI framework.

### 2.2 Part B: Personal AI Stack (The Frontend Integration)

**Definition**: The user-facing suite deployed via helmfile.

**Components**:

- **UI**: OpenWebUI (best-in-class FOSS chat interface)
- **Router**: LiteLLM Proxy (standardizes API calls, handles model switching & cost tracking)
- **Coding**: Copilot Proxy (intercepts IDE traffic, injects personal context)

**Integration**: OpenWebUI connects to MyContextProtocol via:

- **Filter** (runs automatically before each request) - calls `/context/state` to inject user context into System Prompt
- **Tool** (LLM decides to call) - calls `/context/query` when specific knowledge needed

---

## 3. Core Architectural Decisions

### 3.1 Stack Changes from Previous Design

| Component         | Previous                  | Current                               | Rationale                                                                                |
| ----------------- | ------------------------- | ------------------------------------- | ---------------------------------------------------------------------------------------- |
| **FaaS Platform** | OpenFaaS                  | **KEDA + Containers**                 | No framework lock-in, scale-to-zero without gateway overhead, standard Deployments/Jobs  |
| **Queue**         | NATS (OpenFaaS)           | **Dragonfly**                         | Redis-compatible, lower memory footprint, better ARM64 performance, also serves as cache |
| **Postgres**      | Bitnami Helm Chart        | **CloudNativePG Operator**            | Declarative backups, automatic failover, better operator patterns                        |
| **Mem0**          | API Server (ARM64-only)   | **Embedded Library**                  | Avoid ARM64 blocker, direct Python integration, simpler deployment                       |
| **Functions**     | OpenFaaS templates        | **Standard Containers**               | Language-agnostic, standard Dockerfiles, no special runtime                              |
| **Graph Store**   | Considered Neo4j/FalkorDB | **LightRAG + Apache AGE on Postgres** | Purpose-built graph RAG, native Postgres extension, Cypher queries, single database      |

### 3.2 Why KEDA + Containers?

**KEDA** (Kubernetes Event-Driven Autoscaling) provides scale-to-zero without a proprietary FaaS framework.

**Benefits**:

- **Standard Kubernetes primitives**: Deployments, Jobs, CronJobs - no lock-in
- **Scale on anything**: Queue depth, cron schedule, HTTP requests, database queries
- **Language-agnostic**: Any container, any language
- **Lightweight**: No gateway, no custom API, just scaling

**Comparison**:

| Feature       | OpenFaaS              | Knative              | KEDA + Containers            |
| ------------- | --------------------- | -------------------- | ---------------------------- |
| Scale to zero | Yes (Pro reliable)    | Yes                  | Yes                          |
| Lock-in       | High (templates, CLI) | Medium (CRDs)        | **Low** (standard k8s)       |
| Local dev     | Awkward               | Heavy                | **Native** (just containers) |
| Complexity    | Medium                | High (Istio/Kourier) | **Low**                      |

### 3.3 Why Dragonfly?

**Dragonfly** is a modern, high-performance Redis replacement.

**Benefits for this use case**:

- **Redis-compatible API**: KEDA Redis scaler works directly
- **Lower memory footprint**: ~30% less than Redis
- **Better ARM64 performance**: Native ARM64 optimization
- **Single binary**: Simpler deployment than Redis Cluster
- **Dual role**: Queue for ingestion + Cache for Mem0 user context (Phase 2/3)

### 3.4 Why CloudNativePG?

**CloudNativePG** is a Kubernetes operator for PostgreSQL.

**Benefits**:

- **Declarative backups**: Schedule, retention, restore all in YAML
- **Automatic failover**: When scaling to multiple replicas (future)
- **Better operator patterns**: Custom resources for Postgres management
- **Backup to S3/MinIO**: Native support for object storage backups

---

## 4. Memory Architecture: The Three-Tier System

### 4.1 The Core Distinction

The system maintains **three complementary memory tiers** for different types of knowledge:

| Tier                   | Store          | What                                               | Example                                               | Used For                                                   |
| ---------------------- | -------------- | -------------------------------------------------- | ----------------------------------------------------- | ---------------------------------------------------------- |
| **Tier 1: SHORT**      | **Mem0**       | Subjective user facts, preferences, recent context | "User thinks KEDA is hard", "User prefers dark mode"  | **Personalization**, tone, agent behavior                  |
| **Tier 2: LONG**       | **LlamaIndex** | Full documents, semantic search                    | PDFs, documentation, long-form content                | **Document retrieval**, semantic similarity                |
| **Tier 3: RELATIONAL** | **LightRAG**   | Entity relationships, knowledge graph              | "KEDA scales Deployments", "Sarah works on Project X" | **Graph queries**, entity connections, multi-hop reasoning |

**Why This Architecture**:

- **Mem0** captures user preferences and subjective opinions (fast retrieval, <100ms)
- **LlamaIndex** indexes full documents for semantic search (medium speed, ~200-500ms)
- **LightRAG** builds entity graphs for relationship queries (graph traversal, Cypher)
- Clean separation prevents hallucination and confusion

**Example Routing**:

- "What does the user like?" → **Mem0** (subjective preferences)
- "Find documents about KEDA" → **LlamaIndex** (semantic document search)
- "How is KEDA related to Kubernetes?" → **LightRAG** (entity relationships, graph query)
- "What's the user's birthday?" → **LightRAG** (objective fact about user as entity)

### 4.2 The State vs Tools Pattern

This is the **key architectural insight** for building high-quality agents.

#### State (Mem0) - Automatic Middleware

**Access Pattern**: Pre-fetched and injected into System Prompt _before_ the LLM sees the request.

**Latency**: ~50-100ms, happens every request automatically.

**Purpose**: Defines _who the user is_ and _how to respond_.

**Implementation**:

```
User Request → [MIDDLEWARE] → Mem0.search(user_id) → System Prompt Injection → LLM
```

**Example**:

```
System Prompt (injected): "You are a helpful assistant.
USER CONTEXT: User is a Python developer. Prefers concise answers. Hates YAML."

User: "Help me debug this KEDA scaler"

Agent: [Already knows user preferences, responds accordingly]
```

#### Tools (LlamaIndex + LightRAG) - On-Demand Retrieval

**Access Pattern**: Agent _decides_ which tool to call based on query type.

**Latency**: ~200-500ms, only when needed.

**Purpose**: Retrieves knowledge from two specialized stores:

- **Tier 2 (LONG)**: Full documents via LlamaIndex semantic search
- **Tier 3 (RELATIONAL)**: Entity relationships via LightRAG graph queries

**Implementation**:

```
LLM → [Decides "I need documents about X"] → search_documents() → LlamaIndex query → Response
LLM → [Decides "I need relationships for Y"] → query_graph() → LightRAG query → Response
```

**Tool Definitions** (OpenAI-compatible):

**Tool 1: Document Search (LlamaIndex)**

```json
{
  "name": "search_life_os_documents",
  "description": "Search your Knowledge Base for documents, notes, or code snippets using semantic search.",
  "parameters": {
    "type": "object",
    "properties": {
      "query": { "type": "string", "description": "Semantic search query" }
    },
    "required": ["query"]
  }
}
```

**Tool 2: Graph Query (LightRAG)**

```json
{
  "name": "search_life_os_graph",
  "description": "Query the knowledge graph for entities and their relationships (people, events, concepts).",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Entity or relationship query"
      },
      "mode": {
        "type": "string",
        "enum": ["local", "global", "hybrid", "naive"],
        "default": "hybrid"
      }
    },
    "required": ["query"]
  }
}
```

**Why This is Correct**:

- **State is always relevant**: Every response needs user context (tone, preferences) from Mem0
- **Knowledge is conditionally relevant**: Agent chooses which store based on query type
- **Explicit tool selection**: Agent decides documents vs graph (no automatic routing)
- **Efficiency**: Don't query stores for "Hello" messages

### 4.3 Request Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│                     USER REQUEST                             │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  MIDDLEWARE (FastAPI, runs automatically)                    │
│                                                              │
│  1. Extract user_id, recent message history                  │
│  2. Call Mem0: mem0.search(user_id=..., query=...)          │
│  3. Format result as System Prompt injection                 │
│  4. Return enriched prompt to LiteLLM/OpenWebUI              │
│                                                              │
│  Endpoint: POST /context/state                               │
│  Cost: ~50-100ms, always happens                             │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  LLM (sees enriched prompt)                                  │
│                                                              │
│  System: "User is Python dev. Hates YAML. Prefers concise."  │
│  User: "Help me debug this KEDA scaler"                      │
│                                                              │
│  Agent analyzes: "I need technical documentation..."         │
│                                                              │
│  → CHOOSES TOOL: documents or graph?                         │
└──────────────────────┬─────────────┬────────────────────────┘
                       │             │
         ┌─────────────┘             └─────────────┐
         │ Documents                     Graph     │
         ▼                                         ▼
┌────────────────────────────┐   ┌────────────────────────────┐
│  TOOL 1: Document Search   │   │  TOOL 2: Graph Query       │
│  (LlamaIndex)              │   │  (LightRAG)                │
│                            │   │                            │
│  POST /context/query/      │   │  POST /context/query/      │
│       documents            │   │       graph                │
│                            │   │                            │
│  Returns: Full documents,  │   │  Returns: Entities,        │
│  semantic matches          │   │  relationships, context    │
│                            │   │                            │
│  Cost: ~200-500ms          │   │  Cost: ~200-500ms          │
└────────────────────────────┘   └────────────────────────────┘
```

### 4.4 OpenWebUI Integration

**Filter for State (Mem0)**:

```python
# mem0_injector.py (OpenWebUI Filter)
def filter_request(messages, user_id):
    # Call MyContextProtocol /context/state
    response = requests.post(
        "http://mycontextprotocol/context/state",
        json={"user_id": user_id, "recent_messages": messages[-5:]}
    )

    # Prepend to system prompt
    context = response.json()["context"]
    system_msg = {"role": "system", "content": f"USER CONTEXT: {context}"}
    return [system_msg] + messages
```

**Tool 1: Document Search (LlamaIndex)**:

```python
# Registered in OpenWebUI Tools config
{
  "name": "search_life_os_documents",
  "url": "http://mycontextprotocol/context/query/documents",
  "method": "POST",
  "description": "Search your Knowledge Base for documents, notes, and code snippets."
}
```

**Tool 2: Graph Query (LightRAG)**:

```python
# Registered in OpenWebUI Tools config
{
  "name": "search_life_os_graph",
  "url": "http://mycontextprotocol/context/query/graph",
  "method": "POST",
  "description": "Query the knowledge graph for entities and their relationships (people, events, concepts)."
}
```

---

## 5. Data Processing Architecture

### 5.1 The Omni-Worker Pattern

**Decision**: Single worker that handles extraction and routing, rather than micro-workers.

**Why**:

- Simpler deployment (one image, one ScaledJob)
- Single transaction (atomic writes to both Mem0 and LlamaIndex)
- Easier debugging (one log stream)

**When to Split**: Only if processing times diverge significantly or independent scaling needed.

### 5.2 Ingest Flow

```
Client (add-memory API)
   ↓
[FastAPI Gateway] → Validates input → Dragonfly Queue
   ↓
[KEDA monitors queue length]
   ↓ (when queue >= 10 messages OR daily cron)
[Omni-Worker Pod] (Python)
   ↓
[LLM Extraction] → Structured JSON (Pydantic validated)
   ├─ user_fact: "User thinks KEDA is hard"
   └─ knowledge_snippet: "KEDA is an autoscaler"
   ↓
[Parallel Write]
   ├─ Mem0 library → .add_memory() → Postgres (mem0 tables)
   └─ LlamaIndex → .insert() → Postgres (document_store, graph tables)
   ↓
[Mark processed in Dragonfly] → Acknowledge message
```

### 5.3 KEDA Scaling Configuration

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledJob
metadata:
  name: omni-worker
spec:
  jobTargetRef:
    template:
      spec:
        containers:
          - name: worker
            image: mycontextprotocol/omni-worker:latest
  triggers:
    - type: redis # Dragonfly is Redis-compatible
      metadata:
        address: dragonfly.default.svc.cluster.local:6379
        listName: ingest-queue
        listLength: "10" # Batch threshold
    - type: cron
      metadata:
        timezone: UTC
        start: 0 2 * * * # Daily at 2 AM (fallback)
        desiredReplicas: "1"
```

### 5.4 Extraction Schema

```python
from pydantic import BaseModel

class UserFact(BaseModel):
    """Subjective: User preferences, opinions, beliefs"""
    content: str
    confidence: float  # 0.0-1.0
    category: str      # "preference", "opinion", "habit"

class KnowledgeSnippet(BaseModel):
    """Objective: Facts, definitions, events"""
    content: str
    entities: list[str]       # ["KEDA", "Kubernetes"]
    source: str              # URL or "conversation"
    date: str | None

class ExtractionResult(BaseModel):
    user_facts: list[UserFact]
    knowledge_snippets: list[KnowledgeSnippet]
```

**Instructor Usage**:

```python
import instructor
from openai import OpenAI

client = instructor.patch(OpenAI())

result = client.chat.completions.create(
    model="gpt-4",
    response_model=ExtractionResult,
    messages=[
        {"role": "system", "content": "Extract facts. Separate subjective user opinions from objective knowledge."},
        {"role": "user", "content": raw_input}
    ]
)

# result is validated Pydantic model
for fact in result.user_facts:
    mem0.add_memory(fact.content, user_id=user_id)

for snippet in result.knowledge_snippets:
    llamaindex.insert(snippet.content, metadata=snippet.dict())
```

### 5.5 Deduplication Strategy

| Store               | Strategy                   | Implementation                                                         |
| ------------------- | -------------------------- | ---------------------------------------------------------------------- |
| **Dragonfly Queue** | Message ID                 | Built-in Redis deduplication                                           |
| **Mem0**            | Semantic/Entity resolution | Built-in (Mem0 consolidates "User likes coffee" + "User loves coffee") |
| **LlamaIndex**      | Content hash               | Check hash before insert to avoid exact duplicates                     |

```python
# LlamaIndex deduplication
import hashlib

def insert_if_new(content: str, metadata: dict):
    content_hash = hashlib.sha256(content.encode()).hexdigest()

    # Check if exists
    existing = db.execute(
        "SELECT id FROM document_store WHERE content_hash = ?",
        (content_hash,)
    )

    if not existing:
        llamaindex.insert(content, metadata={"hash": content_hash, **metadata})
```

---

## 6. System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACES                                  │
│  (OpenWebUI, CLI, Browser Extension, Copilot Proxy)                     │
└────────────────┬────────────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────────────────┐
│                    CLOUDFLARE TUNNEL (Prod Only)                         │
│             Zero-Trust Ingress, DNS-Failover, DDoS Protection            │
└────────────────┬────────────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────────────────┐
│                      K3S CLUSTER (Kubernetes)                            │
│  Lightweight, single-control-plane, optimized for ARM                    │
├─────────────────────┬────────────────────────────────────────────────────┤
│  MYCONTEXTPROTOCOL  │           DATA LAYER                               │
│  (Part A)           │                                                    │
├─────────────────────┼────────────────────────────────────────────────────┤
│  MYCONTEXTPROTOCOL  │           DATA LAYER                               │
│  (Part A)           │                                                    │
├─────────────────────┼────────────────────────────────────────────────────┤
│ • FastAPI Gateway   │  POSTGRESQL (CloudNativePG + pgvector + AGE):     │
│   - /context/state  │  • Mem0 table (user facts, Tier 1: SHORT)         │
│   - /context/query  │  • data_documents (LlamaIndex, Tier 2: LONG)      │
│                     │  • LIGHTRAG_* + AGE graphs (Tier 3: RELATIONAL)   │
│ • Omni-Worker       │                                                    │
│   (KEDA ScaledJob)  │  DRAGONFLY:                                        │
│                     │  • Ingest queue (list: ingest-queue)              │
│ • LightRAG REST API │  • Cache layer (Phase 2/3: user context cache)    │
│   (Separate service)│                                                    │
│                     │  MinIO (Phase 2/3):                               │
│ • Mem0 (library)    │  • vault-files (PDFs, documents)                  │
│   Embedded in worker│  • vault-exports (backups)                        │
│                     │                                                    │
│ • LlamaIndex        │                                                    │
│   PGVectorStore     │                                                    │
└─────────────────────┴────────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────────────────┐
│               HOST Infrastructure (VM / k3d)                              │
│  • Oracle Cloud ARM (4 OCPU, 24GB RAM) - Production                      │
│  • k3d (Docker) - Local Development                                      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Technology Stack

### 7.1 Core Services

| Component               | Technology                                          | Namespace                   | Role                                                     |
| ----------------------- | --------------------------------------------------- | --------------------------- | -------------------------------------------------------- |
| **Database**            | CloudNativePG (Postgres 16 + pgvector + Apache AGE) | `database`                  | All persistent data (Mem0, LlamaIndex, LightRAG)         |
| **Queue + Cache**       | Dragonfly                                           | `default`                   | Ingest queue + future user context cache                 |
| **Scaling**             | KEDA                                                | `keda-system`               | Scale workers based on queue depth / cron                |
| **Gateway**             | FastAPI (Python)                                    | `default`                   | API endpoints for State and Tools                        |
| **Worker**              | Python container (Mem0 + LlamaIndex)                | `default`                   | Batch processing, extraction, storage                    |
| **Graph RAG**           | LightRAG REST API                                   | `default`                   | Entity extraction, graph queries, relationship traversal |
| **Ingress**             | Cloudflare Tunnel + Traefik                         | `cloudflare`, `kube-system` | Zero-trust HTTPS access                                  |
| **Storage** (Phase 2/3) | MinIO                                               | `storage`                   | S3-compatible object storage for files                   |

### 7.2 Python Libraries (Worker)

| Library        | Purpose                               | Usage                                                  |
| -------------- | ------------------------------------- | ------------------------------------------------------ |
| **Mem0**       | Episodic memory, user facts           | `mem0.add_memory()`, entity resolution, Tier 1 (SHORT) |
| **LlamaIndex** | Document indexing, semantic search    | PGVectorStore for documents, Tier 2 (LONG)             |
| **LightRAG**   | Graph-based RAG, entity relationships | REST API for graph queries, Tier 3 (RELATIONAL)        |
| **instructor** | LLM output validation                 | Structured extraction with Pydantic                    |
| **psycopg2**   | Postgres driver                       | Direct DB access                                       |
| **redis-py**   | Dragonfly client                      | Queue operations                                       |

### 7.3 Why Python for Workers?

| Language   | Verdict               | Rationale                                                                                                                          |
| ---------- | --------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| **Python** | ✅ **Correct choice** | Mem0 is Python-native, LlamaIndex is Python-native, instructor/pydantic mature. Workers are IO-bound (network, DB), not CPU-bound. |
| Go         | ❌                    | Would require calling Python anyway or reimplementing Mem0/LlamaIndex                                                              |
| Rust       | ❌                    | Same problem, no ecosystem for this workload                                                                                       |

**Where Go/Rust makes sense**: The FastAPI gateway, if high throughput needed. But Python FastAPI is fine for MVP.

---

## 8. Database Schema

### 8.1 PostgreSQL Tables

#### Mem0 Tables (Auto-Managed by Library)

Mem0's pgvector provider **automatically creates** its own table. We don't define or migrate this.

```sql
-- Created automatically by Mem0 Python client
-- Collection name: "mem0" (configurable)
CREATE TABLE mem0 (
  id UUID PRIMARY KEY,
  vector vector(768),  -- Dimension matches embedding model
  payload JSONB        -- Contains: user_id, content, category, metadata, timestamps
);

-- Mem0 also creates pgvector extension automatically
CREATE EXTENSION IF NOT EXISTS vector;
```

**Configuration**:

```python
from mem0 import Memory

config = {
    "vector_store": {
        "provider": "pgvector",
        "config": {
            "connection_string": "postgresql://user:password@host:port/database",
            "collection_name": "mem0",  # Table name
            "embedding_model_dims": 768,  # Match your embedding model
        }
    }
}
memory = Memory.from_config(config)
```

#### LlamaIndex Tables (Auto-Managed by Library)

LlamaIndex's PGVectorStore **automatically creates** its tables when `perform_setup=True`.

```sql
-- Created automatically by LlamaIndex PGVectorStore
-- Table name: data_<table_name> (e.g., data_documents)
CREATE TABLE data_documents (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  text VARCHAR NOT NULL,
  metadata_ JSONB,
  node_id VARCHAR,
  embedding VECTOR(768)
  -- If hybrid_search=True:
  -- text_search_tsv TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', text)) STORED
);

-- HNSW index for vector similarity search
CREATE INDEX documents_embedding_idx
  ON data_documents USING hnsw (embedding vector_cosine_ops);

-- If hybrid_search enabled:
-- CREATE INDEX documents_text_search_idx ON data_documents USING gin (text_search_tsv);
```

**Configuration**:

```python
from llama_index.vector_stores.postgres import PGVectorStore

vector_store = PGVectorStore.from_params(
    database="app",
    host="postgresql-cluster-rw.database.svc.cluster.local",
    port=5432,
    user="app",
    password="...",
    table_name="documents",  # Creates data_documents
    embed_dim=768,
    perform_setup=True,  # Auto-create table and indexes
)
```

#### Property Graph Storage (LightRAG + Apache AGE)

**Current Implementation**: LightRAG with Apache AGE (PostgreSQL graph extension).

**Architecture**: Three-tier memory system - Mem0 (short/subjective), LlamaIndex (long/documents), LightRAG (relational/graph).

**Storage Backend**:

- **Apache AGE**: PostgreSQL extension providing graph model with openCypher query support
- **Tables**: `LIGHTRAG_DOC_FULL`, `LIGHTRAG_DOC_CHUNKS`, `LIGHTRAG_VDB_*` (vectors), `LIGHTRAG_LLM_CACHE`, `LIGHTRAG_DOC_STATUS`
- **Graph**: AGE graphs for entity relationships with Cypher queries

**Why LightRAG + AGE?**:

- **Purpose-built for RAG**: LightRAG designed specifically for graph-augmented retrieval
- **Single database**: All three tiers in one PostgreSQL instance (Mem0 + LlamaIndex + LightRAG/AGE)
- **Nix-native**: Apache AGE already in nixpkgs (`pkgs.postgresql_16Packages.age`)
- **CNPG compatible**: Mount via ImageVolume, no custom image build needed
- **Full Cypher**: openCypher query language for graph traversal
- **Modern stack**: LightRAG is cutting-edge (27k stars, Beta but production-ready for pilots)

**Configuration**:

```python
# LightRAG with PostgreSQL backend
rag = LightRAG(
    working_dir=WORKING_DIR,
    llm_model_func=llm_model_func,
    embedding_func=embedding_func,
    graph_storage="PGGraphStorage",
    vector_storage="PGVectorStorage",
    doc_status_storage="PGDocStatusStorage",
    kv_storage="PGKVStorage",
)
await rag.initialize_storages()  # Auto-creates extensions and tables

# Environment variables
POSTGRES_HOST=postgresql-cluster-rw.database.svc.cluster.local
POSTGRES_PORT=5432
POSTGRES_DATABASE=lightrag  # Separate database to avoid table conflicts
POSTGRES_USER=app
POSTGRES_PASSWORD=...
```

**AGE Requirements**:

- PostgreSQL ≥ 16.6
- `CREATE EXTENSION vector` (pgvector - already deployed)
- `CREATE EXTENSION age CASCADE` (Apache AGE - to be added)

**Deployment Strategy**:

1. Build Nix OCI image with AGE extension artifacts
2. Mount into CNPG via ImageVolume pattern
3. Deploy LightRAG as REST API service (isolation, stability)
4. Gateway calls LightRAG API for graph queries

**Query Modes**:

- `local`: Entity-focused retrieval
- `global`: High-level summaries
- `hybrid`: Combined local + global
- `naive`: Simple vector search fallback

#### Application Tables (Managed by Alembic)

These are **our** tables, managed via SQLAlchemy models and Alembic migrations.

```sql
-- Inbox queue (temporary, before processing)
CREATE TABLE inbox (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content TEXT NOT NULL,
  content_hash VARCHAR(64) NOT NULL,
  source VARCHAR(100) NOT NULL,
  target VARCHAR(100) NOT NULL,  -- "mem0", "llamaindex", "both"
  metadata JSONB DEFAULT '{}',
  processed BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  processed_at TIMESTAMPTZ
);

-- Indexes for efficient querying
CREATE INDEX idx_inbox_processed ON inbox(processed, created_at);
CREATE INDEX idx_inbox_created_at ON inbox(created_at DESC);
CREATE UNIQUE INDEX idx_inbox_content_hash ON inbox(content_hash)
  WHERE processed = false;  -- Deduplicate pending items only
```

**Schema Management**:

- **Mem0 & LlamaIndex**: Libraries handle their own schema (no Alembic migrations needed)
- **Application tables**: Managed via `src/mycontextprotocol/models.py` + Alembic
- **Source of truth**: SQLAlchemy models → `alembic revision --autogenerate` → migrations

### 8.2 Dragonfly Data Structures

```
# Ingest queue (Redis LIST)
LPUSH ingest-queue '{"inbox_id": "uuid", "content": "...", "source": "api"}'

# Worker processing
BRPOP ingest-queue 30  # Blocking pop with 30s timeout

# Phase 2/3: User context cache (Redis HASH)
# Key: "user:context:{user_id}"
# TTL: 300 seconds (5 minutes)
HSET user:context:alice "preferences" "Python dev, hates YAML, concise"
EXPIRE user:context:alice 300
```

---

## 9. API Specification

### 9.1 Ingest API

**POST /ingest**

Add new content to the system.

**Request**:

```json
{
  "content": "string (max 1MB)",
  "source": "api|upload|email|web",
  "metadata": {
    "title": "optional",
    "author": "optional",
    "url": "optional",
    "date": "ISO-8601 timestamp"
  }
}
```

**Response** (202 Accepted):

```json
{
  "id": "uuid",
  "status": "queued",
  "message": "Content added to processing queue"
}
```

### 9.2 State API (Middleware)

**POST /context/state**

Retrieve user context for System Prompt injection. Called by OpenWebUI Filter automatically.

**Request**:

```json
{
  "user_id": "string",
  "recent_messages": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ]
}
```

**Response**:

```json
{
  "context": "User is a Python developer. Prefers concise answers. Hates YAML. Working on KEDA project.",
  "cache_hit": false,
  "latency_ms": 87
}
```

### 9.3 Query API (Tools)

Agent explicitly chooses which endpoint to call based on query type.

#### 9.3.1 Document Search (LlamaIndex)

**POST /context/query/documents**

Semantic search over full documents. Called by LLM when it needs document content.

**Request**:

```json
{
  "query": "What is KEDA and how does it work?",
  "limit": 10
}
```

**Response**:

```json
{
  "results": [
    {
      "id": "uuid",
      "content": "KEDA is a Kubernetes event-driven autoscaler...",
      "relevance": 0.89,
      "source": "documentation",
      "metadata": {
        "title": "KEDA Overview",
        "url": "https://..."
      }
    }
  ],
  "query_time_ms": 156,
  "store": "llamaindex"
}
```

#### 9.3.2 Graph Query (LightRAG)

**POST /context/query/graph**

Entity relationship queries. Called by LLM when it needs connections or context.

**Request**:

```json
{
  "query": "How does KEDA relate to Kubernetes resources?",
  "mode": "hybrid", // "local", "global", "hybrid", "naive"
  "limit": 10
}
```

**Response**:

```json
{
  "results": [
    {
      "entities": ["KEDA", "ScaledObject", "Deployment"],
      "relationships": [
        "KEDA manages ScaledObject CRD",
        "ScaledObject scales Deployment based on metrics"
      ],
      "context": "KEDA watches external event sources...",
      "relevance": 0.92
    }
  ],
  "query_time_ms": 203,
  "store": "lightrag",
  "mode_used": "hybrid"
}
```

---

## 10. Deployment Architecture

### 10.1 Infrastructure

**Production**: Oracle Cloud Free Tier

- **Instance**: VM.Standard.A1.Flex (ARM Ampere)
- **Specs**: 4 OCPU, 24GB RAM, 200GB boot + 100GB block storage
- **OS**: Ubuntu 24.04 ARM64
- **K3s**: Single-node cluster (can scale to multi-node later)

**Local Development**: k3d

- **Cluster**: K3s in Docker
- **Resource**: ~8GB RAM allocated to Docker Desktop
- **Parity**: Same manifests, same Helm charts

### 10.2 Deployment Method

**Helmfile** for orchestration:

```yaml
# helmfile.yaml
repositories:
  - name: cnpg
    url: https://cloudnative-pg.github.io/charts
  - name: kedacore
    url: https://kedacore.github.io/charts
  - name: dragonfly
    url: https://www.dragonflydb.io/helm-charts

releases:
  # Database with operator
  - name: cloudnativepg
    namespace: cnpg-system
    chart: cnpg/cloudnative-pg

  - name: postgres-cluster
    namespace: database
    chart: cnpg/cluster
    values:
      - values/postgres.yaml

  # Queue + Cache
  - name: dragonfly
    namespace: default
    chart: dragonfly/dragonfly
    values:
      - values/dragonfly.yaml

  # Autoscaling
  - name: keda
    namespace: keda-system
    chart: kedacore/keda

  # Our application (custom chart)
  - name: mycontextprotocol
    namespace: default
    chart: ./charts/mycontextprotocol
    values:
      - values/common.yaml
      - values/{{ .Environment.Name }}.yaml
```

### 10.3 Container Images

**All images must be linux/arm64** for Oracle Cloud deployment.

**Build strategy**:

```dockerfile
# Gateway (FastAPI)
FROM python:3.12-slim-bookworm
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Multi-arch build**:

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t mycontextprotocol/gateway:latest \
  --push .
```

---

## 11. Implementation Phases

### Phase 1: Core Infrastructure ✅ COMPLETE (2026-01-07)

**Goal**: Deploy base Kubernetes infrastructure with database and queue.

**Tasks**:

- [x] Remove OpenFaaS from helmfile
- [x] Add CloudNativePG operator to helmfile
- [x] Add Dragonfly to helmfile
- [x] Add KEDA to helmfile
- [x] Deploy PostgreSQL cluster with pgvector
- [x] Create database schema (Mem0, LlamaIndex, inbox tables)
- [x] Verify connectivity between components

**Deliverable**: ✅ K3d cluster running with Postgres + Dragonfly + KEDA operational.

### Phase 1.5: Development Toolchain (Current Sprint)

**Goal**: Modernize dev environment with uv, ruff, basedpyright, lefthook, Taskfile, Alembic.

**Tasks**:

- [ ] Update flake.nix (remove faas-cli, add modern tools)
- [ ] Create pyproject.toml (Python 3.13, dependencies, tool configs)
- [ ] Create Taskfile.yml (dev tasks: lint, format, typecheck, db:\*)
- [ ] Create lefthook.yml (pre-commit hooks: ruff, basedpyright)
- [ ] Setup Alembic (migrations from SQLAlchemy models)
- [ ] Update documentation (ARCHITECTURE, DEVELOPMENT, README)

**Deliverable**: Modern Python dev environment with automated quality checks and declarative schema migrations.

### Phase 2: Application Services (Next Sprint)

**Goal**: Build and deploy MyContextProtocol API, worker, and LightRAG integration.

**Tasks**:

- [ ] Add Apache AGE extension to CloudNativePG
  - [ ] Build Nix OCI image with AGE extension artifacts
  - [ ] Configure CNPG ImageVolume mount
  - [ ] Test `CREATE EXTENSION age CASCADE`
- [ ] Create FastAPI gateway service
  - [ ] POST /ingest endpoint (writes to Dragonfly queue)
  - [ ] POST /context/state endpoint (queries Mem0)
  - [ ] POST /context/query endpoint (queries LlamaIndex + LightRAG)
- [ ] Create Omni-Worker container
  - [ ] LLM extraction with instructor + Pydantic
  - [ ] Mem0 library integration (embedded mode)
  - [ ] LlamaIndex PGVectorStore integration (documents only)
  - [ ] Parallel writes to Mem0 + LlamaIndex
- [ ] Deploy LightRAG REST API service
  - [ ] Configure PostgreSQL/AGE backend (separate database)
  - [ ] Create Kubernetes Deployment + Service
  - [ ] Test entity extraction and graph queries
- [ ] Integrate LightRAG into Gateway
  - [ ] Add LightRAG client to /context/query endpoint
  - [ ] Implement query routing (LlamaIndex for docs, LightRAG for graph)
  - [ ] Performance testing
- [ ] Create KEDA ScaledJob for worker
- [ ] Write Nix-based container images (gateway, worker, lightrag)
- [ ] Create Helm chart for mycontextprotocol
- [ ] Deploy and test end-to-end flow

**Deliverable**: Working three-tier memory system: API → Queue → Worker → Postgres (Mem0 + LlamaIndex + LightRAG/AGE)

### Phase 3: Query & Retrieval (Sprint 3)

**Goal**: Implement State and Tools query patterns.

**Tasks**:

- [ ] Implement `/context/state` logic
  - [ ] Query Mem0 for user facts
  - [ ] Format as System Prompt injection
  - [ ] Return within 100ms SLA
- [ ] Implement `/context/query/documents` endpoint (LlamaIndex)
  - [ ] Semantic search over document store
  - [ ] Return ranked document results
- [ ] Implement `/context/query/graph` endpoint (LightRAG)
  - [ ] Graph traversal and entity extraction
  - [ ] Support local/global/hybrid/naive modes
- [ ] Add query result caching (Dragonfly)
- [ ] Performance testing and optimization

**Deliverable**: Both State (middleware) and Tools (agentic) query patterns working.

### Phase 4: Frontend Integration (Sprint 4)

**Goal**: Connect OpenWebUI to MyContextProtocol.

**Tasks**:

- [ ] Write OpenWebUI Filter for `/context/state` (Mem0 injection)
- [ ] Register `/context/query` as OpenWebUI Tool
- [ ] Deploy OpenWebUI via Helmfile
- [ ] Deploy LiteLLM proxy
- [ ] End-to-end testing with real chat interactions

**Deliverable**: Full Personal AI Stack with State + Tools integration working.

### Phase 5: Advanced Features (Future)

**Deferred to Phase 2/3** (after MVP):

- [ ] Dragonfly context cache (cache Mem0 results, 5-30 min TTL)
- [ ] MinIO deployment for file storage
- [ ] Multi-modal ingestion (PDFs, images, audio)
- [ ] Backup strategy (Postgres → MinIO daily)
- [ ] Monitoring and observability (Prometheus, Grafana)

---

## 12. Phase 2/3 Features (Deferred)

### 12.1 Dragonfly Context Cache

**Problem**: Mem0 queries add 50-100ms latency on every request.

**Solution**: Cache recent user context in Dragonfly with short TTL.

**Implementation**:

```python
# In /context/state endpoint
def get_user_context(user_id: str) -> str:
    # Check cache first
    cache_key = f"user:context:{user_id}"
    cached = dragonfly.get(cache_key)

    if cached:
        return cached

    # Cache miss - query Mem0
    context = mem0.search(user_id=user_id)
    formatted = format_for_prompt(context)

    # Cache for 5 minutes
    dragonfly.setex(cache_key, 300, formatted)

    return formatted
```

**Benefit**: Reduces latency from ~100ms to ~5ms for rapid back-and-forth conversations.

**Trade-off**: Context may be stale for up to 5 minutes after new facts learned.

### 12.2 Query Routing Strategies

**Problem**: Should we query Mem0, LlamaIndex, or both?

**Options**:

**A. Router LLM** (decides which store to query):

```python
# Classify query type first
query_type = llm.classify(query, types=["factual", "personal", "mixed"])

if query_type == "personal":
    results = mem0.search(query)
elif query_type == "factual":
    results = llamaindex.query(query)
else:  # mixed
    results = merge(mem0.search(query), llamaindex.query(query))
```

**B. Fan-out** (query both, merge results):

```python
# Always query both in parallel
mem0_results, llamaindex_results = asyncio.gather(
    mem0.search_async(query),
    llamaindex.query_async(query)
)

# Merge and re-rank
results = merge_and_rerank(mem0_results, llamaindex_results)
```

**C. Hierarchical** (check Mem0 first, then LlamaIndex if needed):

```python
# Query Mem0 for user context first
mem0_results = mem0.search(query)

# If not enough results, query knowledge base
if len(mem0_results) < threshold:
    llamaindex_results = llamaindex.query(query)
    results = mem0_results + llamaindex_results
```

**Recommendation**: Start with **Fan-out (B)** for simplicity, optimize to Router (A) if cost becomes an issue.

### 12.3 MinIO File Storage

**Use Case**: Store PDFs, images, documents for later processing or retrieval.

**Schema**:

```
vault-files/
  ├── pdf/document-{uuid}.pdf
  ├── images/{uuid}.jpg
  └── documents/{uuid}.txt

vault-exports/
  ├── backups/postgres-{date}.dump
  └── exports/knowledge-graph-{date}.json
```

**Integration**:

```python
# In Omni-Worker, after extraction
if file_reference in metadata:
    # Store original file
    minio.fput_object(
        bucket="vault-files",
        object_name=f"pdf/{inbox_id}.pdf",
        file_path=temp_file_path
    )

    # Store reference in document_store
    vault_reference = f"s3://vault-files/pdf/{inbox_id}.pdf"
```

---

## 13. Success Criteria

### MVP (Phase 1-4 Complete)

- [ ] Ingestion: POST /ingest → Queue → Worker → Postgres (both Mem0 + LlamaIndex)
- [ ] State: POST /context/state returns user context <100ms
- [ ] Tools: POST /context/query returns relevant results <500ms
- [ ] Frontend: OpenWebUI connected with Filter (State) + Tool (Knowledge)
- [ ] End-to-End: User message → Context injected → LLM response → Tool call (if needed) → Final response

### Phase 2/3 Complete

- [ ] Cache: Dragonfly context cache reduces State latency to <10ms
- [ ] Files: MinIO stores PDFs, Worker processes them
- [ ] Routing: Query routing strategy implemented (Router/Fan-out)
- [ ] Monitoring: Prometheus metrics, Grafana dashboards
- [ ] Backups: Daily Postgres backups to MinIO

---

## 14. Architecture Trade-offs

### Decisions Made

| Decision                      | Trade-off                            | Rationale                                                                   |
| ----------------------------- | ------------------------------------ | --------------------------------------------------------------------------- |
| **Mem0 as library**           | Tighter coupling                     | Avoids ARM64 server blocker, simpler deployment, direct Python access       |
| **Single Omni-Worker**        | Can't scale components independently | Simpler for MVP, atomic transactions, easier debugging                      |
| **KEDA + Containers**         | More K8s complexity than FaaS        | No framework lock-in, standard patterns, language-agnostic                  |
| **LightRAG + Apache AGE**     | Beta software, fewer references      | Purpose-built graph RAG (27k stars), PostgreSQL-native, modern architecture |
| **Dragonfly dual-role**       | Single point of failure              | Redis-compatible, lower resource usage, simple to operate                   |
| **State always queries Mem0** | Latency on every request             | Ensures agent always has user context, can be cached in Phase 2/3           |

### Future Optimization Paths

- **Mem0 to separate service**: If multi-language clients needed
- **Split Omni-Worker**: If processing time imbalance emerges
- **Separate cache service**: If Dragonfly becomes bottleneck

---

## 15. Development Toolchain

### 15.1 Philosophy

**Modern Python with Nix-First Tooling**: All development tools are managed via Nix flake for reproducibility. Python package management uses `uv` for speed, with `uv2nix` bridging to Nix for container builds.

**Declarative Everything**: Schema defined as SQLAlchemy models (code is source of truth), migrations autogenerated via Alembic. Pre-commit hooks and tasks defined in YAML configs.

**No Vendor Lock-In**: Rejected tools with gated "pro" features (Atlas). Prefer open tooling with community support.

### 15.2 Technology Stack

| Category              | Tool               | Purpose                    | Why This Choice                                             |
| --------------------- | ------------------ | -------------------------- | ----------------------------------------------------------- |
| **Python Version**    | 3.13               | Runtime                    | Latest stable with performance improvements                 |
| **Package Manager**   | uv                 | Fast dependency resolution | 10-100x faster than pip, deterministic uv.lock              |
| **Nix Bridge**        | uv2nix             | Python ↔ Nix integration   | Bridges uv.lock to Nix reproducibility (lnbits pattern)     |
| **Type Checker**      | basedpyright       | Static analysis            | Faster than mypy, Pydantic v2 native, strict mode           |
| **Linter/Formatter**  | ruff               | Code quality               | Replaces black+isort+flake8, Rust-fast                      |
| **Pre-commit**        | lefthook           | Git hooks                  | Respects Nix PATH, parallel execution, no cache duplication |
| **Task Runner**       | Taskfile (go-task) | Dev automation             | YAML-based, simpler than Make, cross-platform               |
| **DB Migrations**     | Alembic            | Schema management          | SQLAlchemy models → autogenerate migrations                 |
| **Security**          | GitHub Dependabot  | Dependency updates         | Free, automatic, no local tooling needed                    |
| **Container Builder** | Nix dockerTools    | Image creation             | No Dockerfiles, reproducible, minimal layers                |
| **K8s Debugging**     | k9s + stern        | Cluster inspection         | TUI browser + log streaming                                 |

### 15.3 Development Workflow

```bash
# 1. Enter Nix dev shell
nix develop

# 2. Install Python dependencies
uv sync

# 3. Run quality checks
task check          # Runs: format + lint + typecheck

# 4. Individual checks
task format         # ruff format
task lint           # ruff check
task typecheck      # basedpyright

# 5. Database migrations
task db:autogenerate -- "migration message"  # Generate from SQLAlchemy models
task db:upgrade                              # Apply migrations
task db:downgrade                            # Rollback

# 6. Git hooks (automatic)
git commit          # Runs lefthook: ruff + basedpyright
git push            # Runs lefthook: task check
```

### 15.4 SQLAlchemy + Alembic Pattern

**Source of Truth**: SQLAlchemy models in `src/mycontextprotocol/models.py`

**Workflow**:

1. Define/modify models in Python (e.g., add column, new table)
2. Run `task db:autogenerate -- "description"` → Alembic inspects models, generates migration
3. Review generated migration in `alembic/versions/*.py`
4. Run `task db:upgrade` → Apply to database

**Example**:

```python
# src/mycontextprotocol/models.py
from sqlalchemy import Column, String, TIMESTAMP, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Inbox(Base):
    __tablename__ = "inbox"

    id = Column(UUID, primary_key=True, server_default=text("gen_random_uuid()"))
    content = Column(String, nullable=False)
    source = Column(String(100))
    processed = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=text("now()"))
```

Then: `task db:autogenerate -- "add inbox table"` → migration auto-created.

### 15.5 Pre-commit Hooks (Lefthook)

**Automatic checks on commit/push**:

```yaml
# lefthook.yml
pre-commit:
  parallel: true
  commands:
    format:
      run: ruff format --check {staged_files}
    lint:
      run: ruff check {staged_files}
    typecheck:
      run: basedpyright {staged_files}

pre-push:
  commands:
    full-check:
      run: task check
```

**Benefits**:

- Catches issues before CI
- Respects Nix PATH (unlike pre-commit framework)
- Parallel execution (fast)
- No redundant caches

## 16. Getting Started

### 16.1 Local Development (k3d)

```bash
# 1. Start k3d cluster
k3d cluster create mcp-local

# 2. Deploy infrastructure
cd infra/k8s
helmfile sync

# 3. Wait for services
kubectl wait --for=condition=Ready pod -l app=postgres-cluster -n database --timeout=300s

# 4. Apply schema
kubectl exec -n database postgres-cluster-1 -it -- psql -U postgres < ../../scripts/init-db.sql

# 5. Port-forward for testing
kubectl port-forward -n database svc/postgres-cluster-rw 5432:5432 &
kubectl port-forward -n default svc/dragonfly 6379:6379 &
kubectl port-forward -n default svc/mycontextprotocol-gateway 8000:8000 &

# 6. Test ingestion
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"content": "Test memory", "source": "api"}'

# 7. Verify processing
kubectl logs -n default -l app=omni-worker -f
```

### 16.2 Production Deployment (Oracle Cloud)

See separate DEPLOYMENT.md (to be created in Phase 1).

---

## 17. Summary

mycontextprotocol is architected as a **two-part system**:

1. **MyContextProtocol** (Backend) - Memory-as-a-Service API with KEDA-scaled workers
2. **Personal AI Stack** (Frontend) - OpenWebUI + LiteLLM consuming the memory API

The **three-tier memory architecture** (Mem0 for state, LlamaIndex for documents, LightRAG for graph) prevents memory pollution, while the **State vs Tools pattern** ensures efficient context injection (automatic) and knowledge retrieval (explicit tool selection).

**Key Technologies**:

- **KEDA + Containers** (not OpenFaaS) for scale-to-zero without framework lock-in
- **Dragonfly** (not Redis/NATS) for queue + future cache
- **CloudNativePG** (not Bitnami Helm) for declarative Postgres with backups
- **Mem0 library** (not API server) to avoid ARM64 blocker
- **LightRAG + Apache AGE on Postgres** (not Neo4j) for purpose-built graph RAG

The system is designed for **single-user initially**, with clear paths to multi-user and advanced features in Phase 2/3.
