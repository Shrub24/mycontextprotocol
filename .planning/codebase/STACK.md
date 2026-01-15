# Technology Stack

**Analysis Date:** 2026-01-15

## Languages

**Primary:**
- Python 3.13 - All application code in `src/mycontextprotocol/`

**Secondary:**
- Nix - Dev shell and container builds in `flake.nix`
- YAML - Kubernetes/Helm configuration in `infra/k8s/`
- SQL - Schema models and migrations in `src/mycontextprotocol/models.py`

## Runtime

**Environment:**
- Python 3.13 - Runtime for gateway and worker (`pyproject.toml`)
- Nix dev shell - Tooling and infra CLIs (`flake.nix`)

**Package Manager:**
- uv - Python dependency management (`pyproject.toml`, `uv.lock`)
- Lockfile: `uv.lock`

## Frameworks

**Core:**
- FastAPI - API gateway (`src/mycontextprotocol/gateway.py`)
- Uvicorn - ASGI server (`pyproject.toml`)
- Pydantic Settings - configuration (`src/mycontextprotocol/config.py`)
- SQLAlchemy + Alembic - schema management (`src/mycontextprotocol/models.py`)

**Testing:**
- Pytest + pytest-asyncio - test runner (`pyproject.toml`, `tests/`)
- pytest-cov - coverage enforcement (`.taskfiles/test.yml`)

**Build/Dev:**
- Ruff - lint/format (`pyproject.toml`)
- basedpyright - type checking (`.taskfiles/typecheck.yml`)
- uv2nix + pyproject-nix - Nix integration (`flake.nix`)
- Taskfile - task automation (`Taskfile.yml`)

## Key Dependencies

**Critical:**
- mem0ai - user memory storage (`src/mycontextprotocol/memory/mem0_client.py`)
- llama-index + vector stores - document search (`src/mycontextprotocol/memory/llamaindex_store.py`)
- lightrag-hku - graph RAG service (`src/mycontextprotocol/memory/lightrag_client.py`)
- instructor + openai (Ollama) - structured extraction (`src/mycontextprotocol/worker_llm.py`)

**Infrastructure:**
- redis - Dragonfly queue client (`src/mycontextprotocol/worker.py`)
- psycopg + pgvector - Postgres vector storage (`pyproject.toml`)
- httpx - LightRAG API client (`src/mycontextprotocol/memory/lightrag_client.py`)

## Configuration

**Environment:**
- Pydantic Settings from env vars (`src/mycontextprotocol/config.py`)
- Infra env example in `infra/k8s/.env.example`

**Build:**
- `pyproject.toml` - Python build and tool config
- `flake.nix` - Nix shell and image builds

## Platform Requirements

**Development:**
- Nix + uv for local dev (`flake.nix`, `pyproject.toml`)
- Docker/K8s tooling for infra (`flake.nix`, `infra/k8s/README.md`)

**Production:**
- Kubernetes (k3s) via Helmfile (`infra/k8s/helmfile.yaml`)
- Nix-built OCI images (`nix/images/gateway.nix`, `nix/images/worker.nix`)

---

*Stack analysis: 2026-01-15*
*Update after major dependency changes*
