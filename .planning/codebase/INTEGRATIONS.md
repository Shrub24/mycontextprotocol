# External Integrations

**Analysis Date:** 2026-01-15

## APIs & External Services

**LLM/Embeddings:**
- Ollama - LLM + embeddings via HTTP (`src/mycontextprotocol/worker_llm.py`, `src/mycontextprotocol/memory/llamaindex_store.py`)
  - Auth: none (local service)
  - Endpoints used: OpenAI-compatible completions

**External APIs:**
- LightRAG REST API - graph queries and ingestion (`src/mycontextprotocol/memory/lightrag_client.py`)
  - Auth: optional `X-API-Key` (`LIGHTRAG_API_KEY`)
  - Endpoints used: `/query`, `/documents/text`

## Data Storage

**Databases:**
- PostgreSQL (CloudNativePG) - primary data store (`infra/k8s/helmfile.yaml`)
  - Client: psycopg + SQLAlchemy (`pyproject.toml`, `src/mycontextprotocol/models.py`)
  - Extensions: pgvector; Apache AGE planned

**Caching/Queue:**
- Dragonfly (Redis-compatible) - ingest queue and future cache (`infra/k8s/manifests/dragonfly.yaml`, `src/mycontextprotocol/gateway.py`)

## Authentication & Identity

**Auth Provider:**
- Not detected (no auth middleware in gateway yet)

## Monitoring & Observability

**Logs:**
- stdout logging via Python logging (`src/mycontextprotocol/gateway.py`, `src/mycontextprotocol/worker.py`)

## CI/CD & Deployment

**Hosting:**
- Kubernetes via Helmfile (`infra/k8s/helmfile.yaml`)
- Custom Helm charts for gateway/worker (`infra/k8s/charts/gateway`, `infra/k8s/charts/worker`)

**CI Pipeline:**
- GitHub Actions (`.github/workflows/ci.yml`)
  - Steps: format, lint, typecheck, test with coverage

## Environment Configuration

**Development:**
- Required env vars via Settings (`src/mycontextprotocol/config.py`)
- Infra example envs in `infra/k8s/.env.example`

**Production:**
- Secrets managed via SOPS/age (`infra/k8s/.sops.yaml`, `infra/k8s/secrets/`)

## Webhooks & Callbacks

**Incoming:**
- Not detected

**Outgoing:**
- Not detected

---

*Integration audit: 2026-01-15*
*Update when adding/removing external services*
