# Roadmap: mycontextprotocol

## Overview

The roadmap delivers a backend-only memory system with robust ingestion and retrieval flows, backed by three memory tiers and deployed via Kubernetes. Work proceeds from tooling hygiene to memory initialization, then core ingest/retrieval integration, followed by deployment validation and ops hardening.

## Domain Expertise

None

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Tooling hygiene** - Finalize pre-commit formatting/linting gates
- [ ] **Phase 2: Memory store initialization** - Pgvector/AGE setup + Mem0/LlamaIndex/LightRAG tables
- [ ] **Phase 3: Ingest flow** - Wire gateway ingestion to worker persistence
- [ ] **Phase 4: Memory access endpoints** - Tool/middleware retrieval flows (no UI)
- [ ] **Phase 5: Deploy + e2e validation** - Helmfile + k3d end-to-end local run
- [ ] **Phase 6: Ops hardening** - Observability and runtime guardrails

## Phase Details

### Phase 1: Tooling hygiene
**Goal**: Deterministic formatting and linting gates in pre-commit
**Depends on**: Nothing (first phase)
**Research**: Unlikely (existing patterns)
**Plans**: 2-3 plans

Plans:
- [x] 01-01: Finalize lefthook formatter/linter ordering and staging
- [ ] 01-02: Resolve remaining lint/format config mismatches
- [ ] 01-03: Verify taskfile/CI integration consistency

### Phase 2: Memory store initialization
**Goal**: Initialize Postgres schemas/tables for all memory tiers
**Depends on**: Phase 1
**Research**: Likely (AGE/LightRAG integration)
**Research topics**: Apache AGE in CNPG, pgvector extension install order, LightRAG setup
**Plans**: 2-3 plans

Plans:
- [ ] 02-01: Prepare Postgres image with AGE + pgvector
- [ ] 02-02: Initialize Mem0 + LlamaIndex tables
- [ ] 02-03: Initialize LightRAG tables

### Phase 3: Ingest flow
**Goal**: Complete ingestion pipeline into memory stores via worker
**Depends on**: Phase 2
**Research**: Unlikely (internal patterns)
**Plans**: 2-3 plans

Plans:
- [ ] 03-01: Gateway ingestion endpoint -> queue payload contract
- [ ] 03-02: Worker consumes queue and persists into memory tiers
- [ ] 03-03: Validate ingestion end-to-end

### Phase 4: Memory access endpoints
**Goal**: Expose retrieval flows via tools/middleware (no UI)
**Depends on**: Phase 3
**Research**: Likely (tool/middleware integration)
**Research topics**: MCP/tooling access patterns, LightRAG query usage
**Plans**: 2-3 plans

Plans:
- [ ] 04-01: Mem0 retrieval middleware integration
- [ ] 04-02: LlamaIndex retrieval tools
- [ ] 04-03: LightRAG query endpoints

### Phase 5: Deploy + e2e validation
**Goal**: Confirm full local deployment with real ingest/retrieve flows
**Depends on**: Phase 4
**Research**: Unlikely (helmfile/k3d already used)
**Plans**: 2 plans

Plans:
- [ ] 05-01: Helmfile deployment passes locally
- [ ] 05-02: End-to-end ingest/retrieve validation

### Phase 6: Ops hardening
**Goal**: Observability and runtime guardrails for stability
**Depends on**: Phase 5
**Research**: Likely (observability stack selection)
**Research topics**: SigNoz/Langfuse or alternative lightweight stack
**Plans**: 2 plans

Plans:
- [ ] 06-01: Observability stack integration plan
- [ ] 06-02: Runtime guardrails/alerts

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 2.1 → 3 → 4 → 5 → 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Tooling hygiene | 1/3 | In progress | - |
| 2. Memory store initialization | 0/3 | Not started | - |
| 3. Ingest flow | 0/3 | Not started | - |
| 4. Memory access endpoints | 0/3 | Not started | - |
| 5. Deploy + e2e validation | 0/2 | Not started | - |
| 6. Ops hardening | 0/2 | Not started | - |
