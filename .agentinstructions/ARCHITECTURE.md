# mycontextprotocol Architecture

## 1. Executive Summary

**mycontextprotocol** is a self-hosted personal memory and context management system designed for individuals who want to maintain complete sovereignty over their data while leveraging AI-powered knowledge extraction and search. The system combines a lightweight Kubernetes deployment with intelligent memory management, providing a unified platform for ingesting, processing, and querying personal information at scale.

The core philosophy is **Sovereign + Cloud-Agnostic + Hybrid Intelligence**: users own their infrastructure, can deploy anywhere, and benefit from both vector-based semantic search and AI-extracted knowledge graphs. The system is architected for single-user deployment initially but designed to be self-deployable by others.

**Key Capabilities:**
- **Unified Memory Ingestion** - Capture information from multiple sources (files, documents, notes, web content)
- **Intelligent Processing** - Automatic fact extraction, deduplication, and knowledge graph construction via Mem0
- **Semantic Search** - Vector embeddings with pgvector for context-aware memory retrieval
- **Self-Hosted & Portable** - Run on any Linux VM (locally tested on Oracle Cloud ARM instances)
- **Cloud-Agnostic** - No vendor lock-in; use Oracle Cloud, AWS, or on-premises infrastructure

---

## 2. System Architecture

### 2.1 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACES                                  │
│  (WebUI, CLI, API Clients - Future)                                      │
└────────────────┬────────────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────────────────┐
│                    CLOUDFLARE TUNNEL (Prod Only)                         │
│             Zero-Trust Ingress, DNS-Failover, DDoS Protection            │
└────────────────┬────────────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────────────────┐
│                      K3S CLUSTER (Kubernetes)                            │
│  Lightweight, single-control-plane, optimized for ARM & small instances  │
├─────────────────────┬────────────────────────────────────────────────────┤
│    CORE SERVICES    │           DATA LAYER                               │
├─────────────────────┼────────────────────────────────────────────────────┤
│ • OpenFaaS Gateway  │  THE VAULT (Cold Storage):                         │
│ • Mem0 API Server   │  • MinIO S3-compatible                             │
│ • NATS Queue        │  • Raw files, PDFs, archives                       │
│ • Traefik Ingress   │                                                    │
│                     │  THE LIBRARY (Hot Index):                          │
│ FUNCTIONS:          │  • PostgreSQL + pgvector                           │
│ • process-inbox     │  • Inbox queue, embeddings                         │
│ • embed-doc         │  • Document metadata                               │
│ • add-memory        │                                                    │
│ • query-memory      │  THE BRAIN (Intelligence):                         │
│                     │  • Mem0 Knowledge Graph                            │
│                     │  • Fact extraction cache                           │
│                     │  • Redis cache layer                               │
│                     │  • Qdrant vector store (optional)                  │
└─────────────────────┴────────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────────────────┐
│               HOST Infrastructure (VM / Bare Metal)                       │
│  • Oracle Cloud ARM (4 OCPU, 24GB RAM) - Production                      │
│  • k3d (Docker) - Local Development                                      │
└────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Overview

| Component | Role | Technology | Namespace |
|-----------|------|-----------|-----------|
| **PostgreSQL + pgvector** | Relational database + vector search | PostgreSQL 15 | `database` |
| **MinIO** | S3-compatible object storage | MinIO | `minio` |
| **Mem0 API Server** | AI memory & knowledge graph | Docker image | `mem0` |
| **OpenFaaS** | Serverless function platform | OpenFaaS 14.x | `openfaas` |
| **NATS** | Async message queue | NATS (embedded in OpenFaaS) | `openfaas` |
| **Cloudflare Tunnel** | Zero-trust ingress tunnel | cloudflared | `cloudflare` |
| **Traefik** | Kubernetes ingress controller | Traefik | `kube-system` (k3s built-in) |
| **Redis** | Cache layer (Mem0) | Redis | `mem0` |
| **Qdrant** | Vector database (optional) | Qdrant | `mem0` |

### 2.3 Data Flow

1. **Ingestion**: User submits data via HTTP POST to `add-memory` function or file upload to MinIO
2. **Inbox Queue**: Raw data lands in PostgreSQL `inbox` table with status `pending`
3. **Processing**: `process-inbox` cron function (every 10 minutes):
   - Fetches pending inbox items
   - Routes to Mem0 for fact extraction (if text/document)
   - Or routes to `embed-doc` queue for vector embedding
4. **Storage**: 
   - Raw files → MinIO `vault-files` bucket
   - Processed metadata + embeddings → PostgreSQL `document_store` table
   - Extracted facts + knowledge graph → Mem0 internal DB
5. **Retrieval**: `query-memory` function:
   - Accepts natural language query
   - Generates embedding via Mem0
   - Searches pgvector for similar documents
   - Augments results from Mem0 knowledge graph
   - Returns ranked results

---

## 3. The Tri-Layer Data Model

The architecture separates concerns into three layers, each optimized for its role:

### 3.1 The Vault (Cold Storage)

**Purpose**: Immutable archive of raw source material

**Technology**: MinIO S3-compatible object storage

**What Lives Here**:
- Original PDF documents
- Uploaded image files
- Archived emails
- Long-form text exports
- Backup archives

**Access Pattern**: Infrequent, bulk operations; cold storage tier

**Buckets**:
```
vault-files/          # Raw uploaded files
  └── pdf/
  └── images/
  └── documents/
vault-exports/        # System exports and backups
```

**Why**: Decouples storage from processing. Raw files are immutable and safely archived. Allows rescan/re-process workflows without data loss.

### 3.2 The Library (Hot Index)

**Purpose**: Queryable, indexed data with embeddings for semantic search

**Technology**: PostgreSQL 15 + pgvector extension

**Schema**:

```sql
-- Inbox queue for new content
CREATE TABLE inbox (
  id UUID PRIMARY KEY,
  content TEXT,
  source VARCHAR(100),        -- "upload", "email", "api", etc.
  metadata JSONB,             -- source-specific metadata
  processed BOOLEAN DEFAULT false,
  created_at TIMESTAMP DEFAULT now()
);

-- Processed documents with embeddings
CREATE TABLE document_store (
  id UUID PRIMARY KEY,
  content TEXT,
  embedding vector(1536),     -- OpenAI embeddings
  metadata JSONB,             -- title, source, date, etc.
  vault_reference VARCHAR,    -- S3 path in MinIO
  processed_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT now()
);

-- Vector search on embeddings
CREATE INDEX ON document_store USING ivfflat (embedding vector_cosine_ops);

-- Mem0-managed tables (auto-created by Mem0)
-- mem0_memories       - fact extraction results
-- mem0_entities       - knowledge graph nodes
-- mem0_relationships  - knowledge graph edges
```

**Access Pattern**: Hot, frequent queries; millisecond latency required

**Why**: Separates queryable metadata (fast) from raw content (large). Vector index enables semantic search. JSONB metadata allows flexible schema for different content types.

### 3.3 The Brain (Intelligence)

**Purpose**: Extracted facts, relationships, and knowledge graph for AI-powered retrieval

**Technology**: Mem0 (manages own DB + Redis cache + optional Qdrant)

**What Lives Here**:
- Extracted facts ("John works at Acme Corp")
- Entity relationships ("John" → "WORKS_AT" → "Acme Corp")
- Knowledge graph (hypergraph of entities and relationships)
- Deduplication cache (avoids re-extracting same facts)
- Fact embeddings (semantic search over facts)

**Access Pattern**: High-frequency semantic queries; LLM-augmented

**Why**: Mem0 specializes in memory management for LLMs. Handles:
- Fact extraction with context preservation
- Automatic deduplication (same fact in different forms)
- Relationship discovery (who knows whom, what relates to what)
- Contextual retrieval (find facts relevant to a query)

### 3.4 Data Flow Through Layers

```
User Input
  ↓
[Inbox] → store raw + metadata
  ↓
process-inbox (cron /10min)
  ├─ Extract facts → [Brain] via Mem0 API
  ├─ Generate embeddings → [Library] pgvector
  └─ Archive raw → [Vault] MinIO
  ↓
Query Request
  ↓
query-memory Function
  ├─ Search [Library] pgvector → documents
  ├─ Query [Brain] → facts + context
  └─ Merge + rank → results
```

### 3.5 Data Location Summary

| Data Type | Layer | Storage | Latency | Query Pattern |
|-----------|-------|---------|---------|---------------|
| Raw files | Vault | MinIO S3 | Seconds | By path/ID |
| Metadata + embeddings | Library | PostgreSQL | Milliseconds | Vector similarity, full-text |
| Facts + relationships | Brain | Mem0 + Redis | Milliseconds | Semantic, LLM-augmented |
| Cache | Brain | Redis | Microseconds | Hot-set facts |

---

## 4. Infrastructure

### 4.1 Production Environment

**Host**: Oracle Cloud Free Tier VM

**Instance Type**: `VM.Standard.A1.Flex` (ARM-based)
- **vCPU**: 4 ARM OCPU (Ampere A1 cores)
- **Memory**: 24 GB RAM
- **Storage**: 200 GB boot volume (system) + 100 GB block storage (data)
- **Network**: Public IP + VCN with security groups
- **Cost**: Free tier eligible (not charged if within limits)

**Why ARM?**
- Oracle Cloud Free Tier offers ARM instances exclusively
- 4x cheaper than comparable x86 instances
- Modern software (especially containers) has excellent ARM support
- K3s runs extremely well on ARM

**K3s Installation** (via cloud-init):
```bash
#!/bin/bash
curl -sfL https://get.k3s.io | sh -
# Sets KUBECONFIG=/etc/rancher/k3s/k3s.yaml
# Starts immediately with systemd
```

**Production Storage**:
- PostgreSQL: 50 GB persistent volume (production.yaml)
- MinIO: 100 GB (block storage mounted)
- System: 20 GB overhead

**Networking**:
- Cloudflare Tunnel handles all ingress
- No public ports exposed directly
- Tunnel bridges K3s Traefik to Cloudflare network
- DNS configured at Cloudflare dashboard

### 4.2 Local Development

**Host**: Developer's laptop/workstation

**Setup**: k3d (K3s in Docker)

```bash
# Create k3d cluster matching production
k3d cluster create mycontextprotocol \
  --agents 1 \
  --image rancher/k3s:latest \
  --port 8080:80@loadbalancer \
  --port 8443:443@loadbalancer
```

**Resource Allocation** (Docker Desktop defaults):
- Memory: ~16 GB allocated to Docker
- CPU: ~8 cores
- Storage: 100 GB disk image

**Key Differences from Production**:
| Aspect | Local (k3d) | Production (Oracle) |
|--------|------------|-------------------|
| Access | `localhost:8080` | Cloudflare tunnel |
| Ingress | NodePort | Cloudflare Tunnel |
| Storage | Ephemeral (can mount local) | Persistent volumes |
| Networking | Docker bridge | VCN security groups |
| Secrets | env vars | Kubernetes Secrets |

**Local Workflow**:
```bash
cd infra/k8s

# Start cluster
k3d cluster create mycontextprotocol

# Deploy services
helmfile sync

# Access services
kubectl port-forward -n database svc/postgresql 5432:5432
kubectl port-forward -n openfaas svc/gateway 8080:8080
kubectl port-forward -n mem0 svc/mem0 8080:8080

# Check logs
kubectl logs -n openfaas deploy/gateway
kubectl logs -n mem0 deploy/mem0

# Clean up
k3d cluster delete mycontextprotocol
```

### 4.3 Why K3s?

**Decision**: Use K3s (lightweight Kubernetes) instead of faasd or Docker Compose

**Comparison Table**:

| Criterion | K3s | faasd | Docker Compose |
|-----------|-----|-------|-----------------|
| **RAM Overhead** | ~1.5 GB | ~200 MB | ~100 MB |
| **Helm Ecosystem** | ✅ Full | ❌ No | ❌ No |
| **Portability** | ✅ Standard K8s | ❌ Custom | ❌ Host-dependent |
| **Multi-Node** | ✅ Easy | ⚠️ Manual | ❌ No |
| **Production-Ready** | ✅ Yes | ⚠️ For FaaS only | ⚠️ Limited |
| **Stateful Services** | ✅ Excellent | ⚠️ Basic | ✅ Good |
| **Observability** | ✅ Rich | ⚠️ Limited | ⚠️ Basic |
| **Secrets Management** | ✅ Native | ❌ No | ⚠️ Manual |

**Why K3s over Alternatives?**

1. **Helm Ecosystem**: Can use battle-tested charts from Bitnami, OpenFaaS, and Mem0. Avoids reimplementing deployments.

2. **Unification**: Single orchestration for all components (databases, functions, services). No need to manage Docker Compose + separate function runtime.

3. **Portability**: Same manifests work on 24GB Oracle VM, 4GB Raspberry Pi, or 256GB datacenter cluster. Zero drift.

4. **Future-Proof**: Kubernetes is the industry standard. Skills and tools transfer to other projects. GitOps paths (ArgoCD) available.

5. **Stateful Services**: PostgreSQL + MinIO require persistent storage, replication, and recovery. K3s handles this natively.

6. **Worth the 1.5GB**: For a personal memory system where RAM headroom is important, 1.5GB is justified by:
   - No custom integration code needed
   - No operational surprises (uses standard tooling)
   - Can scale to multi-node later
   - Saves 10+ hours of custom orchestration work

**RAM Budget** (24 GB total):
```
K3s control plane          ~1.5 GB
PostgreSQL                 ~1.0 GB (base, grows with data)
Mem0 server                ~2.0 GB (AI model in memory)
OpenFaaS gateway/worker    ~0.3 GB
NATS messaging             ~0.15 GB
MinIO                      ~0.5 GB (metadata, configurable)
Functions (running)        ~1.0 GB (headroom for concurrent)
Qdrant (optional)          ~1.0 GB (if enabled)
OS/system                  ~2.0 GB
────────────────────────────────────
Available headroom         ~14 GB
```

---

## 5. Core Services

### 5.1 PostgreSQL + pgvector

**Role**: Primary relational database + vector search backend

**Deployment**: Helm chart `bitnami/postgresql` v15.0.0

**Kubernetes Namespace**: `database`

**Key Configuration**:
```yaml
# Helm values (helmfile.yaml)
auth:
  database: myapp
  username: myapp
  password: changeme123        # Override in production!

primary:
  persistence:
    enabled: true
    size: 10Gi (dev) / 50Gi (prod)
    storageClass: local-path   # k3s default

initdb:
  scripts:
    init.sql:
      CREATE DATABASE mem0;    # For Mem0 usage
      GRANT ALL PRIVILEGES ON DATABASE mem0 TO myapp;
```

**Database Schema**:

```sql
-- Inbox queue for new content
CREATE TABLE inbox (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content TEXT NOT NULL,
  source VARCHAR(100),         -- "api", "upload", "email", etc.
  metadata JSONB DEFAULT '{}', -- source-specific data
  processed BOOLEAN DEFAULT false,
  created_at TIMESTAMP DEFAULT now(),
  processed_at TIMESTAMP NULL
);

-- Processed document store with embeddings
CREATE TABLE document_store (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content TEXT,
  embedding vector(1536),      -- OpenAI or similar embeddings
  metadata JSONB DEFAULT '{}', -- {title, author, date, source}
  vault_reference VARCHAR,     -- S3 path (s3://vault-files/pdf/...)
  processed_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT now()
);

-- Vector index for semantic search
CREATE INDEX idx_embedding_cosine 
  ON document_store USING ivfflat (embedding vector_cosine_ops);

-- Create pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;
```

**Connection Details**:
- **Host**: `postgresql.database.svc.cluster.local` (internal K8s DNS)
- **Port**: 5432
- **User**: `myapp`
- **Password**: Stored in K8s Secret `postgresql-secret`
- **Databases**: `myapp` (app data), `mem0` (Mem0 data)

**Persistence**:
- Uses K3s `local-path` storage class
- Data stored at `/var/lib/rancher/k3s/storage/` on host
- Backed up separately (future: implement backup strategy)

**Access from Cluster**:
```bash
# Port-forward for local access
kubectl port-forward -n database svc/postgresql 5432:5432

# Connect via psql
psql -h localhost -U myapp -d myapp -p 5432
```

### 5.2 MinIO (S3-Compatible Object Storage)

**Role**: Immutable archive for raw files (The Vault)

**Status**: Planned (not yet deployed in helmfile)

**Proposed Configuration**:
```yaml
# To be added to helmfile.yaml
- name: minio
  namespace: minio
  chart: bitnami/minio
  version: ~12.0.0
  values:
    - values/minio-values.yaml
  set:
    - name: auth.rootUser
      value: minioadmin
    - name: auth.rootPassword
      value: ${MINIO_ROOT_PASSWORD}  # Set via env
    - name: persistence.size
      value: 100Gi
```

**Buckets**:
```
vault-files/          # Raw uploaded files
  ├── pdf/
  ├── documents/
  ├── images/
  └── email/
vault-exports/        # Backups and exports
```

**Features**:
- S3-compatible API (drop-in replacement)
- Built-in versioning and WORM (Write-Once-Read-Many)
- Multipart upload support for large files
- Replication support (future: cross-node)

**Usage from Functions**:
```python
# In embed-doc or process-inbox function
from minio import Minio

client = Minio(
    "minio.minio.svc.cluster.local:9000",
    access_key="minioadmin",
    secret_key=os.getenv("MINIO_PASSWORD")
)

# Upload file
client.fput_object("vault-files", "pdf/document.pdf", "/tmp/file")

# Retrieve file
client.fget_object("vault-files", "pdf/document.pdf", "/tmp/output")
```

### 5.3 Mem0 API Server

**Role**: AI-powered memory management, fact extraction, knowledge graph

**Deployment**: Docker image `mem0ai/mem0` deployed via Helm

**Kubernetes Namespace**: `mem0`

**Key Configuration**:
```yaml
replicaCount: 1 (dev) / 2 (prod)

image:
  repository: mem0ai/mem0
  tag: latest

service:
  type: ClusterIP
  port: 8080

resources:
  requests:
    memory: 256Mi (dev) / 512Mi (prod)
    cpu: 100m (dev) / 250m (prod)
  limits:
    memory: 512Mi (dev) / 1Gi (prod)

# Depends on PostgreSQL
postgresql:
  enabled: false
  host: postgresql.database.svc.cluster.local
  port: 5432
  database: mem0
  username: myapp

# Optional: Qdrant vector store
qdrant:
  enabled: true
  persistence:
    size: 5Gi

# Cache layer
redis:
  enabled: true
  master:
    persistence:
      size: 1Gi
```

**API Endpoints**:
```
POST /api/v1/memories    - Add memory
GET  /api/v1/memories    - Retrieve memories
POST /api/v1/history     - Get conversation history
POST /api/v1/search      - Search knowledge graph
```

**Integration Points**:

1. **process-inbox function** calls Mem0 to extract facts:
```python
import requests

MEM0_HOST = "mem0.mem0.svc.cluster.local:8080"

def extract_facts(text, conversation_id):
    response = requests.post(
        f"http://{MEM0_HOST}/api/v1/memories",
        json={
            "conversation_id": conversation_id,
            "messages": [{"role": "user", "content": text}]
        }
    )
    return response.json()
```

2. **query-memory function** retrieves facts:
```python
def search_facts(query):
    response = requests.post(
        f"http://{MEM0_HOST}/api/v1/search",
        json={"query": query}
    )
    return response.json()["results"]
```

**Data Managed by Mem0**:
- Facts extracted from conversations
- Entity relationships (knowledge graph)
- Deduplication cache
- User conversation history

**Why Mem0?**
- Specialized for LLM memory management
- Automatic deduplication (prevents duplicate facts)
- Relationship discovery (finds connections between entities)
- Contextual retrieval (returns facts relevant to query)
- Production-ready (used by major LLM products)

### 5.4 OpenFaaS (Serverless Functions Platform)

**Role**: Execution runtime for custom business logic functions

**Deployment**: Helm chart `openfaas/openfaas` v14.0.0

**Kubernetes Namespace**: `openfaas`, `openfaas-fn` (function namespace)

**Key Configuration**:
```yaml
gateway:
  replicas: 1 (dev) / 2 (prod)
  service:
    type: NodePort (local) / ClusterIP (prod with tunnel)
    nodePort: 31112

queueWorker:
  replicas: 1 (dev) / 2 (prod)

# Async functions via NATS
nats:
  enabled: true
  # NATS is embedded, no external dependency

# Autoscaling based on function demand
autoscaler:
  enabled: true
```

**Function Namespaces**:
- `openfaas-fn`: User-defined functions
- `openfaas`: Core gateway + worker components

**Function Invocation**:

```bash
# Synchronous (HTTP)
curl -X POST http://localhost:8080/function/query-memory \
  -H "Content-Type: application/json" \
  -d '{"query": "What do I know about AI?"}'

# Asynchronous (via NATS queue)
curl -X POST http://localhost:8080/async-function/embed-doc \
  -H "Content-Type: application/json" \
  -d '{"file_id": "doc-123"}'
```

**Built-in Features**:
- Function versioning
- Zero-scaling (scale to zero when idle)
- Metrics collection (Prometheus-ready)
- Request/response logging
- Health checks and recovery

---

## 6. Functions Specification

Functions are the business logic layer. All are Python-based, deployed to OpenFaaS.

### 6.1 add-memory (HTTP POST)

**Purpose**: Ingest new content into system

**Trigger**: HTTP POST from user/API

**Input**:
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

**Output**:
```json
{
  "id": "uuid",
  "status": "queued",
  "message": "Memory added to inbox"
}
```

**Logic**:
```
1. Validate input (content non-empty, source recognized)
2. Generate UUID for record
3. Store in inbox table (status: pending)
4. Return ID for tracking
5. Function returns immediately (user gets quick feedback)
```

**Dependencies**:
- PostgreSQL connection
- Pydantic for validation

**Code Location**: `functions/add-memory/`

### 6.2 process-inbox (Cron, every 10 minutes)

**Purpose**: Process pending inbox items, route to extraction/embedding

**Trigger**: Cron schedule `*/10 * * * *`

**Execution**:
- Runs every 10 minutes
- Processes batch of up to 100 pending items
- No input parameters (reads from inbox table)

**Logic**:
```
1. FETCH from inbox WHERE processed = false LIMIT 100
2. FOR EACH item:
   a. IF source in [email, notes, text]:
      - Call Mem0 /api/v1/memories (fact extraction)
      - Store facts in knowledge graph
      - Mark processed
   b. ELSE IF source in [pdf, document, upload]:
      - Read from MinIO (if file reference)
      - Call embed-doc function (async, via NATS queue)
      - Mark queued
3. UPDATE inbox SET processed = true WHERE processed_at IS NOT NULL
```

**Dependencies**:
- PostgreSQL (read inbox)
- Mem0 (for fact extraction)
- OpenFaaS NATS (queue embed-doc)
- MinIO (retrieve file content)

**Idempotency**: Yes (marked with processed_at timestamp)

**Code Location**: `functions/process-inbox/`

**Environment Variables**:
```bash
MEM0_API_HOST=mem0.mem0.svc.cluster.local:8080
PG_HOST=postgresql.database.svc.cluster.local
PG_USER=myapp
PG_PASS=${PG_PASSWORD}  # From Secret
NATS_URL=nats://nats.openfaas.svc.cluster.local:4222
```

### 6.3 embed-doc (Async via NATS queue)

**Purpose**: Generate vector embeddings for documents

**Trigger**: Async (NATS message from process-inbox)

**Input** (NATS message):
```json
{
  "inbox_id": "uuid",
  "content": "document text",
  "metadata": {"title": "...", "source": "..."}
}
```

**Output**: None (updates database)

**Logic**:
```
1. RECEIVE message from NATS queue
2. Split content into chunks (512 tokens, 50% overlap)
3. FOR EACH chunk:
   a. Call embedding service (OpenAI or local)
      - API: POST /v1/embeddings with model=text-embedding-3-small
   b. Insert into document_store:
      - id, content, embedding, metadata, vault_reference
   c. Store vault reference if file in MinIO
4. UPDATE inbox SET processed = true
5. Log completion
```

**Error Handling**:
- Retry on API failure (3 attempts with exponential backoff)
- Store failed IDs in `dead_letter_queue` table
- Alerting (future: send to monitoring system)

**Dependencies**:
- OpenAI API (or local embedding service)
- PostgreSQL
- MinIO (optional, for large files)

**Resource Requirements**:
- Memory: 256 MB per concurrent invocation
- CPU: 100 mCPU per invocation
- Network: ~200ms per embedding request

**Code Location**: `functions/embed-doc/`

**Environment Variables**:
```bash
OPENAI_API_KEY=${OPENAI_API_KEY}
EMBEDDING_MODEL=text-embedding-3-small
PG_HOST=postgresql.database.svc.cluster.local
```

### 6.4 query-memory (HTTP GET/POST)

**Purpose**: Search memories across all layers

**Trigger**: HTTP GET/POST from user

**Input**:
```json
{
  "query": "What do I know about AI?",
  "limit": 10,
  "include_metadata": true,
  "search_mode": "hybrid"  # semantic, facts, or hybrid
}
```

**Output**:
```json
{
  "results": [
    {
      "type": "document",
      "id": "uuid",
      "content": "...",
      "relevance": 0.89,
      "source": "upload"
    },
    {
      "type": "fact",
      "id": "uuid",
      "content": "AI can process large amounts of data",
      "context": ["Machine Learning", "Data Processing"],
      "relevance": 0.85
    }
  ],
  "query_time_ms": 156
}
```

**Logic**:
```
1. PARSE query, validate limit (max 100)
2. GENERATE embedding of query (same model as document embeddings)
3. IF search_mode in [semantic, hybrid]:
   a. SEARCH pgvector for similar documents
      - SELECT * FROM document_store
      - WHERE 1 - (embedding <=> query_embedding) > threshold
      - ORDER BY similarity DESC
      - LIMIT limit
4. IF search_mode in [facts, hybrid]:
   a. CALL Mem0 /api/v1/search
      - POST {"query": query_text}
      - Returns facts ranked by relevance
5. MERGE results, de-duplicate, rank by relevance score
6. RETURN results with metadata
```

**Hybrid Search**: Combines vector similarity (documents) + semantic search (facts)
- Vector results weighted 0.6
- Fact results weighted 0.4
- Re-ranked by combined score

**Dependencies**:
- PostgreSQL pgvector
- Mem0 API
- OpenAI API (for query embedding)

**Latency SLA**: < 500ms for typical query

**Code Location**: `functions/query-memory/`

---

## 7. Deployment

### 7.1 OpenTofu Infrastructure-as-Code

**Status**: Planned (structure defined, not yet fully populated)

**Directory**: `infra/tofu/`

**Purpose**: Provision VM and network infrastructure (Oracle Cloud)

**Components** (planned):

```hcl
# main.tf
terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 5.0"
    }
  }
}

# Network
resource "oci_core_vcn" "main" {
  cidr_block = "10.0.0.0/16"
}

resource "oci_core_subnet" "main" {
  vcn_id = oci_core_vcn.main.id
  cidr_block = "10.0.1.0/24"
}

# Security Group
resource "oci_core_network_security_group" "main" {
  vcn_id = oci_core_vcn.main.id
  rules = [
    { ingress, TCP 22 (SSH) },
    { ingress, TCP 443 (HTTPS from Cloudflare) },
    { egress, all }
  ]
}

# VM Instance (ARM)
resource "oci_core_instance" "k3s_server" {
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  compartment_id      = var.compartment_id
  
  instance_options {
    are_legacy_imds_endpoints_disabled = false
  }
  
  shape = "VM.Standard.A1.Flex"
  
  shape_config {
    ocpus         = 4
    memory_in_gbs = 24
  }
  
  source_details {
    source_type             = "IMAGE"
    source_id               = data.oci_core_images.ubuntu.images[0].id
    boot_volume_size_in_gbs = 200
  }
  
  metadata = {
    user_data = base64encode(file("${path.module}/cloud-init.yaml"))
  }
}

# Block storage for data
resource "oci_core_volume" "data" {
  availability_domain = oci_core_instance.k3s_server.availability_domain
  compartment_id      = var.compartment_id
  size_in_gbs         = 100
}

resource "oci_core_volume_attachment" "data" {
  attachment_type = "paravirtualized"
  instance_id     = oci_core_instance.k3s_server.id
  volume_id       = oci_core_volume.data.id
  device          = "/dev/oracleoci/oraclevdb"
}

# Outputs
output "instance_public_ip" {
  value = oci_core_instance.k3s_server.public_ip
}
```

**cloud-init.yaml** (user-data script):
```yaml
#!/bin/bash
# Update system
apt-get update && apt-get upgrade -y

# Install K3s
curl -sfL https://get.k3s.io | sh -

# Wait for K3s to be ready
sleep 10
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

# Prepare data volume
mkfs.ext4 /dev/oracleoci/oraclevdb
mkdir -p /mnt/data
mount /dev/oracleoci/oraclevdb /mnt/data
echo "/dev/oracleoci/oraclevdb /mnt/data ext4 defaults 0 2" >> /etc/fstab

# Create local-path storage provisioner config
mkdir -p /mnt/data/k3s-storage
kubectl patch storageclass local-path -p '{"provisioner":"rancher.io/local-path"}'
```

**Deploy**:
```bash
cd infra/tofu
tofu init
tofu plan -var="compartment_id=ocid1.compartment..."
tofu apply
# Outputs: instance_public_ip
```

### 7.2 Helmfile: Helm Release Management

**File**: `infra/k8s/helmfile.yaml`

**Purpose**: Define and manage all Helm chart deployments

**Helm Repositories**:
```yaml
repositories:
  - name: bitnami
    url: https://charts.bitnami.com/bitnami
  - name: openfaas
    url: https://openfaas.github.io/faas-netes/
  - name: cloudflare
    url: https://cloudflare.github.io/helm-charts
  - name: mem0
    url: https://charts.mem0.ai
```

**Releases Defined**:
1. **postgresql** - Bitnami PostgreSQL chart
2. **openfaas** - OpenFaaS platform
3. **cloudflared** - Cloudflare Tunnel ingress
4. **mem0** - Mem0 AI server
5. **minio** (planned) - MinIO S3 storage

**Values Hierarchy**:
```
helmfile.yaml              (base: repository URLs, versions)
  ├── values/postgresql-values.yaml
  ├── values/openfaas-values.yaml
  ├── values/mem0-values.yaml
  └── environments/
      ├── default.yaml      (dev settings: 1 replica, 10Gi storage)
      └── production.yaml   (prod settings: HA, 50Gi storage, resources)
```

**Deployment**:

```bash
cd infra/k8s

# List releases
helmfile list

# Dry-run (show what will be deployed)
helmfile diff

# Deploy to default environment (local dev)
helmfile sync

# Deploy to production
helmfile -e production sync

# Deploy specific release
helmfile -l name=postgresql sync

# Upgrade all
helmfile apply

# Destroy
helmfile destroy
```

**Key Features**:

- **Templating**: Supports env vars like `${CLOUDFLARE_ACCOUNT_ID}`
- **Secrets**: Injected at deploy time (not stored in git)
- **Selective Sync**: Deploy only changed releases
- **Diff Preview**: Review changes before applying

### 7.3 Plain YAML Manifests (Future)

**Status**: Not yet implemented; for components with custom behavior

**Purpose**: When Helm charts don't provide enough flexibility

**Example** (not in use yet):
```yaml
# mem0-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mem0
  namespace: mem0
spec:
  replicas: 2
  selector:
    matchLabels:
      app: mem0
  template:
    metadata:
      labels:
        app: mem0
    spec:
      containers:
      - name: mem0
        image: mem0ai/mem0:latest
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: database-url
```

**When Used**:
- Custom init containers
- Non-standard configurations
- Custom resource types (e.g., Prometheus ServiceMonitor)
- CronJobs for scheduled functions

---

## 8. Networking & Security

### 8.1 Ingress Architecture

**Local Development** (k3d):
```
User Browser
  ↓
localhost:8080 (k3d port mapping)
  ↓
K3s Service (NodePort 31112)
  ↓
OpenFaaS Gateway / mem0 API
```

**Production** (Oracle Cloud):
```
User Browser
  ↓
HTTPS (any domain)
  ↓
Cloudflare Tunnel
  ├─ DDoS Protection
  ├─ DNS Failover
  └─ Zero-Trust Authentication
  ↓
cloudflared Pod (K8s)
  ↓
Traefik Ingress Controller (built-in K3s)
  ├─ Route by hostname
  ├─ TLS termination (Cloudflare origin cert)
  └─ Load balance across pods
  ↓
Service Endpoints
  ├─ openfaas.example.com → OpenFaaS Gateway
  ├─ mem0.example.com → Mem0 API
  ├─ api.example.com → Custom API (future)
```

**DNS Configuration** (Cloudflare dashboard):
```
openfaas.example.com    CNAME    k3s-cluster.example.com
mem0.example.com        CNAME    k3s-cluster.example.com
api.example.com         CNAME    k3s-cluster.example.com
```

**Tunnel Setup**:
```bash
# Create tunnel (one-time)
cloudflared tunnel create k3s-cluster

# Configure routing
cloudflared tunnel route dns k3s-cluster openfaas.example.com
cloudflared tunnel route dns k3s-cluster mem0.example.com

# Deploy credentials
kubectl create secret generic cloudflare-tunnel \
  --namespace cloudflare \
  --from-file=credentials.json=~/.cloudflare/k3s-cluster.json
```

### 8.2 Secrets Management

**Storage**: Kubernetes Secrets (etcd), encrypted at rest (OpenTofu setup)

**Secrets Required**:

| Secret | Namespace | Key | Used By |
|--------|-----------|-----|---------|
| `postgresql-secret` | database | password | PostgreSQL, Mem0 |
| `openai-api-key` | openfaas-fn | api-key | embed-doc, query-memory |
| `mem0-secrets` | mem0 | api-key | Mem0 API startup |
| `cloudflare-tunnel` | cloudflare | credentials.json | cloudflared pod |
| `minio-secret` | minio | root-password | MinIO admin |

**Creating Secrets**:

```bash
# Create and apply (do NOT commit to git!)
kubectl create secret generic postgresql-secret \
  --namespace database \
  --from-literal=password=<secure-random-password>

kubectl create secret generic openai-api-key \
  --namespace openfaas-fn \
  --from-literal=api-key=sk-...

# Reference in Helm values
# mem0-values.yaml:
env:
  - name: OPENAI_API_KEY
    valueFrom:
      secretKeyRef:
        name: openai-api-key
        key: api-key
```

**No Secrets in Git**:
- `.gitignore` excludes `*.secret.yaml`
- `values/` checked into git (no sensitive data)
- Secrets created manually post-deployment or via CI/CD secrets

### 8.3 Single-User Model

**Current Architecture**: No authentication

**Rationale**: 
- Designed for single user, single device initially
- System runs behind Cloudflare Tunnel (already authenticated at network layer)
- Future: Add Cloudflare Access for multi-user

**Future Enhancements** (planned but not implemented):

1. **Cloudflare Access**:
```yaml
# cloudflared-values.yaml (future)
cloudflare:
  accessPolicy:
    - domain: openfaas.example.com
      emails: ["user@example.com"]
```

2. **Kubernetes RBAC** (for multi-user cluster):
```yaml
# user-role.yaml (future)
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: openfaas-fn
  name: function-deployer
rules:
  - apiGroups: [""]
    resources: ["pods", "logs"]
    verbs: ["get", "list"]
```

3. **API Token Authentication** (future):
```python
# In function handlers
def validate_token(request):
    token = request.headers.get("Authorization")
    # Validate against secret store
    if not token_valid(token):
        raise Unauthorized()
```

**Security Posture (Current)**:
- ✅ Network isolation (Cloudflare Tunnel)
- ✅ HTTPS encryption (Cloudflare + K8s)
- ✅ No public IP exposure
- ❌ No user-level authentication
- ❌ No request signing

---

## 9. Implementation Phases

Recommended development and deployment order:

### Phase 1: Infrastructure Foundation (Week 1-2)

**Goal**: Get K3s cluster running with persistent storage

**Tasks**:
1. ☐ Set up Oracle Cloud account and free tier VM
2. ☐ Write OpenTofu manifests for VM provisioning
3. ☐ SSH into VM, verify K3s installation
4. ☐ Configure kubectl locally to access cluster
5. ☐ Test persistent volumes (local-path storage class)
6. ☐ Set up git repository with infra/ directory

**Deliverable**: K3s cluster running, kubectl access works

### Phase 2: Core Services Deployment (Week 2-3)

**Goal**: Deploy database, messaging, and function platform

**Tasks**:
1. ☐ Add Bitnami repository to Helm
2. ☐ Deploy PostgreSQL via helmfile
3. ☐ Verify PostgreSQL connectivity, create databases
4. ☐ Add OpenFaaS repository
5. ☐ Deploy OpenFaaS gateway + worker
6. ☐ Configure OpenFaaS basic auth
7. ☐ Test function deployment (hello-world)

**Deliverables**:
- PostgreSQL running, accessible
- OpenFaaS gateway accessible on NodePort
- NATS queue working within cluster

### Phase 3: Mem0 Integration (Week 3-4)

**Goal**: Add AI memory layer

**Tasks**:
1. ☐ Add Mem0 chart repository
2. ☐ Deploy Mem0 via helmfile
3. ☐ Configure PostgreSQL connectivity
4. ☐ Verify Mem0 API endpoints
5. ☐ Test fact extraction API
6. ☐ Set up Mem0 secrets (API keys if required)

**Deliverable**: Mem0 API responding to fact extraction requests

### Phase 4: Function Development (Week 4-5)

**Goal**: Implement custom business logic functions

**Functions to Build** (in order of dependency):
1. ☐ **add-memory**: Insert data into inbox
2. ☐ **process-inbox**: Cron job, routes items to extraction
3. ☐ **embed-doc**: Generate embeddings, store in pgvector
4. ☐ **query-memory**: Semantic search across all layers

**Testing**:
- Unit tests for each function
- Integration tests with PostgreSQL + Mem0
- Load testing (concurrent requests)

**Deliverable**: All 4 functions deployed and operational

### Phase 5: Data Layer & Storage (Week 5-6)

**Goal**: Set up file storage and vector search

**Tasks**:
1. ☐ Design PostgreSQL schema (inbox, document_store, etc.)
2. ☐ Deploy MinIO for S3-compatible storage
3. ☐ Create MinIO buckets (vault-files, vault-exports)
4. ☐ Test MinIO integration from functions
5. ☐ Implement pgvector index creation
6. ☐ Test embedding + vector search

**Deliverable**: Files stored in MinIO, embeddings searchable via pgvector

### Phase 6: Ingress & Networking (Week 6-7)

**Goal**: Expose system securely to users

**Tasks** (Local Dev):
1. ☐ Configure k3d port forwarding
2. ☐ Test function invocation via HTTP

**Tasks** (Production):
1. ☐ Create Cloudflare tunnel
2. ☐ Configure tunnel credentials
3. ☐ Deploy cloudflared controller
4. ☐ Set up DNS routing (CNAME → tunnel)
5. ☐ Test HTTPS access to functions
6. ☐ Secure with API keys / Cloudflare Access (future)

**Deliverable**: Functions accessible via HTTPS domains

### Phase 7: Client Integration (Week 7-8, Future)

**Goal**: Build user-facing interfaces

**Options**:
- CLI tool (Python Click)
- Web UI (React/Next.js)
- Telegram bot
- Email integration
- Browser extension

**Status**: Out of scope for initial deployment

---

## 10. Prerequisites

### Accounts & Credentials

| Account | Purpose | Free Tier |
|---------|---------|-----------|
| **Oracle Cloud** | VM hosting | Yes (4 OCPU, 24GB RAM, 200GB storage) |
| **Cloudflare** | Tunnel ingress, DNS | Yes (free plan + tunnel feature) |
| **GitHub** | Code repository | Yes |
| **OpenAI** | Embedding model | Requires payment ($0.02 per 1M tokens) |

### Software Tools (Local Machine)

```bash
# Install all prerequisites
brew install kubernetes-cli helm helmfile      # macOS
# OR
apt-get install kubectl helm helmfile          # Linux

# Install additional tools
brew install tofu                               # OpenTofu (Terraform fork)
brew install k3d                                # K3s in Docker (local dev)
faas-cli                                        # OpenFaaS CLI
docker                                          # Docker Desktop or podman

# Verify installations
kubectl version --client
helm version
helmfile --version
k3d version
tofu version
```

### Required Secrets

**Before Deploying Production**:

1. **Cloudflare Tunnel** (for production only)
   ```bash
   cloudflared tunnel login
   cloudflared tunnel create k3s-cluster
   export CLOUDFLARE_ACCOUNT_ID="<account-id>"
   export CLOUDFLARE_TUNNEL_SECRET="<secret-from-json>"
   ```

2. **Oracle Cloud API Credentials** (for OpenTofu)
   ```bash
   # Download from Oracle Cloud console
   ~/.oci/config          # API key config
   ~/.oci/oci_api_key.pem # Private key
   ```

3. **OpenAI API Key**
   ```bash
   # Create at https://platform.openai.com/account/api-keys
   export OPENAI_API_KEY="sk-..."
   ```

4. **PostgreSQL Password** (generate random)
   ```bash
   export PG_PASSWORD="$(openssl rand -base64 32)"
   ```

### Environment Variables

**Create `.env` file** (local development):
```bash
export CLOUDFLARE_ACCOUNT_ID="your-account-id"
export CLOUDFLARE_TUNNEL_SECRET="your-tunnel-secret"
export OPENAI_API_KEY="sk-..."
export PG_PASSWORD="secure-random-password"
export MINIO_ROOT_PASSWORD="minioadmin-password"
```

**Load before deployment**:
```bash
source .env
helmfile sync
```

---

## 11. Future Enhancements

### Short-term (1-2 months)

- **MinIO Deployment**: Add S3-compatible storage to helmfile
- **Data Persistence**: Implement backup strategy (daily snapshots to S3)
- **Observability**: Add Prometheus + Grafana for monitoring
- **Function Lifecycle**: Implement function versioning, canary deployments
- **Local Embeddings**: Replace OpenAI with local model (Ollama) to reduce costs

### Medium-term (3-6 months)

- **GitOps**: Implement ArgoCD for continuous deployment
- **Multi-region**: Add replication to second K3s cluster
- **Kustomize**: Transition from plain Helm to Kustomize for more flexibility
- **Client Integrations**: Build CLI, web UI, browser extension
- **Advanced Search**: Add full-text search (PostgreSQL FTS) alongside vector search

### Long-term (6+ months)

- **Multi-user**: Add per-user namespaces, RBAC, authentication
- **Scaling**: Migrate to full Kubernetes cluster (3+ nodes)
- **Replication**: Cross-region failover, multi-master setup
- **Observability**: Distributed tracing (Jaeger), centralized logging (ELK)
- **Analytics**: Dashboards showing memory coverage, search patterns

### Potential Integrations

- **Email Ingestion**: Automatically import emails as memories
- **Browser Extension**: Clip web articles, sync to mycontextprotocol
- **Voice Input**: Transcribe voice notes → memory inbox
- **Calendar Integration**: Sync events, meeting notes
- **External APIs**: Notion, Obsidian, Roam Research sync
- **OpenWebUI Integration**: Self-hosted web interface for querying memories and managing context
- **ChatGPT/LLM Client Adapters**: API adapters for ChatGPT, Claude, and other LLM clients to query personal memory
- **Copilot Proxy**: GitHub Copilot-compatible proxy that injects personal context into code completions
- **Codex CLI Proxy**: Command-line interface proxy for OpenAI Codex with personal memory augmentation

---

## 12. Resource Allocation Summary

### Memory Budget (24 GB Oracle VM)

```
┌─────────────────────────────────────────────────────────┐
│ Total Available: 24 GB                                  │
├─────────────────────────────────────────────────────────┤
│ K3s System:                         ~1.5 GB │███░░░░░░│
│ PostgreSQL + indexes:               ~1.0 GB │██░░░░░░░│
│ Mem0 (model in memory):             ~2.0 GB │████░░░░░│
│ OpenFaaS gateway + workers:         ~0.3 GB │░░░░░░░░░│
│ NATS messaging:                     ~0.15 GB│░░░░░░░░░│
│ MinIO:                              ~0.5 GB │█░░░░░░░░│
│ Function execution headroom:        ~1.0 GB │██░░░░░░░│
│ Qdrant (optional):                  ~1.0 GB │██░░░░░░░│
│ Redis cache:                        ~0.2 GB │░░░░░░░░░│
│ OS + System:                        ~2.0 GB │████░░░░░│
├─────────────────────────────────────────────────────────┤
│ Available Headroom:                 ~13 GB  │██████████│
└─────────────────────────────────────────────────────────┘
```

### CPU Allocation

| Component | Dev (request) | Dev (limit) | Prod (request) | Prod (limit) |
|-----------|---------------|------------|----------------|--------------|
| PostgreSQL | 250m | 500m | 500m | 1000m |
| Mem0 | 100m | 500m | 250m | 1000m |
| OpenFaaS Gateway | 50m | 200m | 100m | 200m |
| Functions | 50m | 200m | 100m | 500m |
| NATS | 50m | 200m | 50m | 200m |
| Total Requested | ~500m | - | ~1000m | - |

**4 OCPU = 4000m**, so we use ~25% of CPU at normal load with plenty of headroom for spikes.

### Storage Budget

| Component | Dev | Prod | Notes |
|-----------|-----|------|-------|
| PostgreSQL | 10 GB | 50 GB | Grows with data |
| MinIO | 50 GB | 100 GB | Grows with files |
| System | 20 GB | 20 GB | OS + K3s |
| Free Space | 20 GB | 30 GB | Buffer for growth |

---

## 13. Troubleshooting Quick Reference

### Cluster Issues

```bash
# Check cluster status
kubectl cluster-info
kubectl get nodes

# Check all pods across namespaces
kubectl get pods --all-namespaces

# Check service status
kubectl get svc --all-namespaces

# Check persistent volumes
kubectl get pv
kubectl get pvc --all-namespaces
```

### PostgreSQL

```bash
# Port-forward
kubectl port-forward -n database svc/postgresql 5432:5432

# Connect
psql -h localhost -U myapp -d myapp

# Check logs
kubectl logs -n database -l app.kubernetes.io/name=postgresql
```

### OpenFaaS

```bash
# Get gateway password
kubectl get secret -n openfaas basic-auth -o jsonpath="{.data.basic-auth-password}" | base64 --decode

# Port-forward gateway
kubectl port-forward -n openfaas svc/gateway 8080:8080

# Check function pods
kubectl get pods -n openfaas-fn

# View function logs
kubectl logs -n openfaas-fn deployment/<function-name>
```

### Mem0

```bash
# Port-forward
kubectl port-forward -n mem0 svc/mem0 8080:8080

# Check logs
kubectl logs -n mem0 deployment/mem0

# Test API
curl http://localhost:8080/health
```

### Network

```bash
# Test DNS within cluster
kubectl run -it --rm debug --image=nicolaka/netshoot --restart=Never -- sh
# Inside pod:
nslookup postgresql.database.svc.cluster.local
curl http://mem0.mem0.svc.cluster.local:8080/health
```

### Helm

```bash
# List releases
helm list --all-namespaces

# Check release status
helm status postgresql -n database

# View values
helm get values postgresql -n database

# Rollback release
helm rollback postgresql -n database
```

---

## 14. Getting Started

### Quick Start (Local Development)

```bash
# 1. Clone repository
git clone https://github.com/yourname/mycontextprotocol.git
cd mycontextprotocol

# 2. Start K3s cluster locally
k3d cluster create mycontextprotocol

# 3. Install Helm dependencies
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add openfaas https://openfaas.github.io/faas-netes/
helm repo update

# 4. Deploy services
cd infra/k8s
helmfile sync

# 5. Wait for pods to be ready
kubectl wait --for=condition=Ready pod -l app=postgresql -n database --timeout=300s

# 6. Port-forward services
kubectl port-forward -n database svc/postgresql 5432:5432 &
kubectl port-forward -n openfaas svc/gateway 8080:8080 &

# 7. Test
curl -X GET http://localhost:8080/function/query-memory

# 8. Cleanup
k3d cluster delete mycontextprotocol
```

### Production Deployment

```bash
# 1. Set up OpenTofu
cd infra/tofu
tofu init
tofu apply -var="compartment_id=<your-compartment-id>"
# Note: instance IP from output

# 2. SSH into VM
ssh ubuntu@<instance-ip>

# 3. K3s should be auto-installed, verify
sudo k3s kubectl get nodes

# 4. Copy kubeconfig to local machine
scp ubuntu@<instance-ip>:/etc/rancher/k3s/k3s.yaml ~/.kube/config-prod

# 5. Update kubeconfig with correct IP
sed -i '' "s/127.0.0.1/<instance-ip>/g" ~/.kube/config-prod

# 6. Deploy via Helmfile
KUBECONFIG=~/.kube/config-prod helmfile -e production sync

# 7. Configure Cloudflare Tunnel
cloudflared tunnel create k3s-cluster
# Follow prompts, get credentials

# 8. Deploy tunnel to cluster
kubectl create secret generic cloudflare-tunnel \
  -n cloudflare \
  --from-file=credentials.json=~/.cloudflare/k3s-cluster.json

# 9. Deploy cloudflared
KUBECONFIG=~/.kube/config-prod helmfile -e production -l name=cloudflared sync

# 10. Test
curl https://openfaas.yourdomain.com/
```

---

## Appendix: File Structure

```
mycontextprotocol/
├── .agentinstructions/
│   └── ARCHITECTURE.md              # This file
├── .beads/                          # Issue tracking config
├── docs/                            # Additional documentation
├── functions/                       # OpenFaaS function definitions
│   ├── add-memory/
│   ├── process-inbox/
│   ├── embed-doc/
│   └── query-memory/
├── infra/
│   ├── tofu/                        # OpenTofu IaC (VM provisioning)
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── cloud-init.yaml
│   └── k8s/                         # Kubernetes + Helmfile
│       ├── helmfile.yaml             # Helm release definitions
│       ├── values/                   # Chart values (dev defaults)
│       │   ├── postgresql-values.yaml
│       │   ├── openfaas-values.yaml
│       │   ├── mem0-values.yaml
│       │   └── cloudflared-values.yaml
│       ├── environments/             # Environment-specific configs
│       │   ├── default.yaml          # Local dev settings
│       │   └── production.yaml       # Prod settings
│       └── README.md                 # Deployment instructions
├── scripts/                         # Utility scripts
├── README.md                        # Project overview
├── AGENTS.md                        # Agent instructions
└── .gitignore
```

---

## Summary

mycontextprotocol is a **sovereign, cloud-agnostic personal memory system** built on:

- **Infrastructure**: K3s on Oracle Cloud ARM (or local k3d)
- **Data**: PostgreSQL + pgvector (structured) + MinIO (files) + Mem0 (intelligence)
- **Processing**: OpenFaaS serverless functions
- **Ingress**: Cloudflare Tunnel (zero-trust)

The tri-layer data model (**Vault + Library + Brain**) separates storage concerns while enabling powerful semantic search and AI-driven retrieval. The architecture is designed to be self-hosted, portable, and extensible.

Implementation follows a phased approach, starting with infrastructure, then core services, then functions and data layer integration. The system is ready for single-user deployment and can be extended to multi-user with proper authentication and RBAC.

For questions, see the troubleshooting section or review specific component documentation in sections 5-6.
