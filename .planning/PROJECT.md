# mycontextprotocol

## What This Is

mycontextprotocol is a backend-only memory and context system: a FastAPI gateway + async worker that ingest conversation/history and persist memory across three tiers (Mem0 state, LlamaIndex document memory, LightRAG graph memory). It is accessed via middleware, tools/plugins, and hooks (no UI), with ingestion handled by a worker that extracts/sorts from full context/history.

## Core Value

Reliable, extensible memory systems that stay modular, lightweight, and decoupled while remaining modern and idiomatic.

## Requirements

### Validated

- ✓ FastAPI gateway with ingestion + context endpoints — existing
- ✓ Async worker pipeline via Dragonfly queue — existing
- ✓ Three-tier memory clients (Mem0, LlamaIndex, LightRAG) — existing
- ✓ Kubernetes + Helmfile deployment structure — existing
- ✓ Nix-based dev shell + uv toolchain — existing

### Active

- [ ] Initialize memory store tables for Mem0, LlamaIndex, LightRAG in Postgres
- [ ] Ensure infra lint/format hooks are reliable and deterministic
- [ ] Finish gateway + worker integration for ingestion and retrieval flows

### Out of Scope

- Frontend/UI/dashboard — memory is accessed via middleware/tools/hooks only
- Product UX polish — no web UI or client application work

## Context

The system is split into gateway and worker layers with queue-driven ingestion (Dragonfly), and three memory tiers backed by Postgres and LightRAG. Deployment is infra-first (Kubernetes via Helmfile). Tooling relies on a Nix dev shell and modern Python workflow (ruff + basedpyright + uv). The project prioritizes modular, decoupled components and modern idioms over legacy patterns.

## Constraints

- **Architecture**: Modular, lightweight, decoupled systems are mandatory
- **Workflow**: Prefer modern, idiomatic tooling and practices (SOTA)
- **Dev Environment**: Nix + direnv preferred as current best approach, but can change if a better modern workflow emerges
- **Interface**: No frontend; memory access is via middleware/tools/hooks only

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Backend-only (no UI) | Memory is accessed via middleware/tools/hooks | — Pending |
| Three-tier memory (Mem0/LlamaIndex/LightRAG) | Clear separation of state, semantic, and graph memory | — Pending |
| Nix-based dev shell + uv toolchain | Modern, reproducible workflow | — Pending |

---
*Last updated: 2026-01-15 after initialization*
