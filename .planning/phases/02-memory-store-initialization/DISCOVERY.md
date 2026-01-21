# Phase 2 Discovery: Memory store initialization

## Decisions locked
- Multi-database layout inside CNPG cluster (separate DBs for mem0, llamaindex, lightrag, and app-owned tables).
- One shared Postgres role + password ("app") stored via SOPS-managed Secrets.
- LightRAG API key required in all environments (consistent behavior).
- Linkerd/mTLS deferred to Phase 6 unless secrets become a blocker.

## Current repo signals
- CNPG cluster uses image `ghcr.io/shrub24/mycontextprotocol:postgres-age-latest` (Nix-built Postgres 17 with AGE + pgvector).
- CNPG bootstrap currently creates `myapp` database and owner from `postgresql-credentials` secret.
- Gateway/worker Helm values reference databases `mem0` and `llamaindex` with user `app`.
- LightRAG values reference database `lightrag` with user `app` and expect `lightrag-secrets`.

## Extension needs
- pgvector required for mem0 + llamaindex.
- AGE required for LightRAG graph storage only.
- Extensions are per-database; DB creation must ensure vector (and age where required) exist in each DB.

## Planned bootstrap approach
- Use CNPG bootstrap SQL to create databases (`mem0`, `llamaindex`, `lightrag`, `mycontextprotocol`) owned by `app`.
- Install `vector` in mem0 + llamaindex (+ lightrag if needed).
- Install `age` in lightrag only.

## Risks/notes
- Current Alembic revision drops Mem0/LlamaIndex tables on upgrade; must be corrected to avoid deleting self-managed tables.
- Helmfile currently references LightRAG chart at `/tmp/...`; decision is to vendor the chart into the repo for reproducibility and pin updates.
