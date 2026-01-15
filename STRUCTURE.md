# Project Structure

## Directory Layout

```
/mnt/LinuxData/Projects/dev/mycontextprotocol/
├── .agentinstructions/          # Agent-specific documentation
│   └── ARCHITECTURE.md         # Full system architecture (1307+ lines)
├── infra/                      # Infrastructure as Code
│   ├── k8s/                    # Kubernetes manifests and Helm
│   │   ├── bases/              # Kustomize bases
│   │   ├── charts/             # Helm charts (gateway, worker)
│   │   ├── environments/       # Environment-specific configs
│   │   ├── helmfile.yaml       # Multi-environment deployment orchestration
│   │   ├── manifests/          # Raw Kubernetes manifests
│   │   ├── secrets/            # Encrypted secrets (SOPS)
│   │   └── values/             # Helm values files
│   └── tofu/                   # Terraform/OpenTofu (empty)
├── nix/                        # Nix package management
│   └── images/                 # Container image definitions
│       ├── gateway.nix         # FastAPI gateway image
│       ├── postgres-age.nix    # PostgreSQL with AGE extension
│       └── worker.nix          # Omni-worker image
├── src/                        # Source code
│   └── mycontextprotocol/      # Main Python package
│       ├── config.py           # Application configuration
│       ├── gateway.py          # FastAPI gateway service (9153 lines)
│       ├── health.py           # Health check endpoints
│       ├── memory/             # Memory tier implementations
│       │   ├── lightrag_client.py  # LightRAG graph queries
│       │   ├── llamaindex_store.py # LlamaIndex document search
│       │   └── mem0_client.py      # Mem0 episodic memory
│       ├── models.py           # SQLAlchemy database models
│       ├── worker_llm.py       # LLM extraction logic
│       └── worker.py           # Omni-worker batch processor
├── tests/                      # Test suite
├── alembic/                    # Database migrations
├── k3d/                        # Local K3s cluster configs
├── scripts/                    # Utility scripts (empty)
└── Configuration files:
    ├── flake.nix               # Nix flake (development environment)
    ├── pyproject.toml          # Python project configuration
    ├── uv.lock                 # Python dependency lockfile
    ├── Taskfile.yml            # Task runner configuration
    ├── lefthook.yml            # Git hooks configuration
    ├── .yamllint.yaml          # YAML linting rules
    └── .yamlfmt.yaml           # YAML formatting rules
```

## Key Files and Their Purposes

### Core Application
- `src/mycontextprotocol/gateway.py` - FastAPI service exposing `/context/state` and `/context/query` endpoints
- `src/mycontextprotocol/worker.py` - KEDA-scaled batch processor handling LLM extraction and storage
- `src/mycontextprotocol/models.py` - SQLAlchemy models for inbox queue and application tables

### Memory Tiers
- `src/mycontextprotocol/memory/mem0_client.py` - Tier 1: Subjective user memory (preferences, opinions)
- `src/mycontextprotocol/memory/llamaindex_store.py` - Tier 2: Document storage and semantic search
- `src/mycontextprotocol/memory/lightrag_client.py` - Tier 3: Entity relationships and graph queries

### Infrastructure
- `infra/k8s/helmfile.yaml` - Orchestrates deployment of all services (CNPG, Dragonfly, KEDA, LightRAG, gateway, worker)
- `nix/images/gateway.nix` - Container image definition for FastAPI gateway
- `nix/images/worker.nix` - Container image definition for Omni-worker
- `flake.nix` - Nix development environment with all tools (uv, ruff, basedpyright, etc.)

### Configuration
- `pyproject.toml` - Python 3.13, dependencies, tool configurations
- `Taskfile.yml` - Development tasks (check, install, dev, deploy)
- `lefthook.yml` - Pre-commit hooks for code quality
- `alembic.ini` - Database migration configuration

## Architecture Pattern: Gateway + Worker + Stores

### Components
1. **API Gateway** (`gateway.py`) - FastAPI service handling HTTP requests
2. **Omni-Worker** (`worker.py`) - Single container processing all extraction and routing
3. **Three Memory Stores**:
   - **Mem0** (PostgreSQL table) - User preferences and subjective facts
   - **LlamaIndex** (PGVectorStore) - Document indexing and semantic search
   - **LightRAG** (Apache AGE) - Entity relationships and knowledge graphs

### Data Flow
```
Client Request → FastAPI Gateway → Dragonfly Queue → KEDA ScaledJob → Omni-Worker → Parallel Writes
                                                                                     ↓
                                                                       ┌──────────────┴──────────────┐
                                                                       │ PostgreSQL (CloudNativePG) │
                                                                       └──────────────┬──────────────┘
                                                                                      ↓
                                                            ┌─────────────┬────────────┴─────────────┬─────────────┐
                                                            │   Mem0      │     LlamaIndex          │   LightRAG   │
                                                            │ (Tier 1)    │     (Tier 2)            │   (Tier 3)   │
                                                            │ Subjective  │     Documents           │   Relational │
                                                            └─────────────┴─────────────────────────┴─────────────┘
```

### Key Layers and Entry Points

#### Entry Points
- **HTTP API**: `/ingest` (POST), `/context/state` (POST), `/context/query/*` (POST)
- **Queue**: Dragonfly (Redis-compatible) LIST for ingestion pipeline
- **Database**: PostgreSQL with extensions (pgvector, AGE) for all persistent storage

#### Processing Layers
1. **Gateway Layer**: Request validation, routing, response formatting
2. **Worker Layer**: LLM extraction with instructor/Pydantic, parallel storage writes
3. **Storage Layer**: Three specialized stores with different query patterns

### Infrastructure Layout

#### Container Images (Nix-built)
- `gateway:latest` - FastAPI + Uvicorn
- `worker:latest` - Python + Mem0 + LlamaIndex + LightRAG client
- `postgres-age:latest` - PostgreSQL 16 + AGE extension

#### Kubernetes Services
- **cnpg-cluster** (database) - PostgreSQL with pgvector and AGE
- **dragonfly** (queue) - Redis-compatible queue and cache
- **keda** (scaling) - Event-driven autoscaling
- **lightrag** (graph) - REST API for graph queries
- **gateway** (api) - FastAPI service
- **worker** (processing) - KEDA ScaledJob for batch processing

#### Deployment Orchestration
- **Helmfile**: Multi-environment deployment management
- **Kustomize**: Environment-specific customizations
- **SOPS**: Secret encryption and management

## Development Workflow

### Quality Gates
- **Pre-commit**: lefthook runs ruff format/check + basedpyright on staged files
- **Pre-push**: task check runs full codebase validation
- **CI**: pytest + coverage + infrastructure checks

### Toolchain
- **Python**: 3.13 with uv for dependency management
- **Code Quality**: ruff (format/lint), basedpyright (types)
- **Database**: SQLAlchemy models → Alembic migrations
- **Containers**: Nix dockerTools for reproducible images
- **K8s**: helmfile + Kustomize for GitOps-style deployments</content>
<parameter name="filePath">STRUCTURE.md