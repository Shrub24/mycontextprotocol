# mycontextprotocol Architecture (Agent Summary)

This repository contains **Part A only**: the MyContextProtocol backend (gateway, worker, memory stores, and infra manifests). Part B (OpenWebUI/LiteLLM, etc.) is out of scope and referenced only for integration context.

## Current Architecture Source of Truth

The up-to-date architecture map and data flow live in:
- `.planning/codebase/ARCHITECTURE.md`
- `.planning/codebase/INTEGRATIONS.md`

Use those documents for current system design, dependencies, and deployment structure.

## Core Concepts (High Level)

- **State vs Tools pattern**: Mem0 state is injected automatically; LlamaIndex + LightRAG are explicit tools.
- **Gateway + Worker**: FastAPI gateway handles API requests; async worker consumes Dragonfly queue and writes to memory stores.
- **Infra-first deployment**: Kubernetes via Helmfile, with CNPG (Postgres), Dragonfly, KEDA, LightRAG, and app charts.
