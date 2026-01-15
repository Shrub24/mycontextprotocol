# Codebase Concerns

**Analysis Date:** 2026-01-15

## Tech Debt

**Import-time settings:**
- Issue: `LlamaIndexSettings.model_validate({})` runs at import time
- Why: Settings created as module-level constant
- Impact: Tests and tooling require env vars before import
- Fix approach: Lazy-init settings in `create_llamaindex_store()`
- File: `src/mycontextprotocol/memory/llamaindex_store.py`

**Infra docs drift:**
- Issue: `infra/k8s/README.md` still references legacy OpenFaaS
- Impact: Confusing for new contributors
- Fix approach: Update README to reflect Helmfile-only deployment
- File: `infra/k8s/README.md`

## Known Bugs

**Test fragility around env vars:**
- Symptoms: Tests fail if required env vars missing
- Trigger: Running pytest without env setup
- Workaround: Set env vars in `tests/conftest.py`
- File: `tests/conftest.py`

## Security Considerations

**Secrets management:**
- Risk: Misconfigured secrets can leak if committed
- Current mitigation: SOPS config in `infra/k8s/.sops.yaml`
- Recommendation: Ensure all secrets stay in `infra/k8s/secrets/`

## Performance Bottlenecks

**LLM extraction latency:**
- Problem: Per-task LLM call in worker
- Cause: Synchronous extraction for each queue item
- Improvement path: Batch extraction or async parallelism
- File: `src/mycontextprotocol/worker_llm.py`

## Fragile Areas

**External service dependency chain:**
- Why fragile: Gateway and worker depend on Dragonfly, Postgres, LightRAG, Ollama
- Common failures: Startup failures when any service is unavailable
- Safe modification: Use health checks and retries
- Test coverage: Limited integration tests
- Files: `src/mycontextprotocol/gateway.py`, `src/mycontextprotocol/worker.py`

## Scaling Limits

**Queue-driven worker scaling:**
- Limit: Worker scaling depends on KEDA + Dragonfly queue depth
- Symptoms at limit: Backlog growth if extraction is slow
- Scaling path: Increase KEDA concurrency, add batching
- Files: `infra/k8s/charts/worker/templates/scaledjob.yaml`

## Dependencies at Risk

**Apache AGE extension (planned):**
- Risk: Not yet deployed in CNPG cluster
- Impact: LightRAG graph storage may fail without extension
- Migration plan: Add AGE to CNPG image or ImageVolume
- Files: `infra/k8s/values/cnpg-cluster/*`, `infra/k8s/helmfile.yaml`

## Missing Critical Features

**E2E deployment verification:**
- Problem: No automated end-to-end test
- Blocks: Confident release validation
- Implementation complexity: Medium (k3d + helmfile + smoke tests)
- Files: `infra/k8s/README.md`

## Test Coverage Gaps

**Storage client tests:**
- What's not tested: Mem0/LlamaIndex/LightRAG clients
- Risk: API changes could break silently
- Priority: Medium
- Difficulty to test: Requires mocking external services
- Files: `src/mycontextprotocol/memory/*`

---

*Concerns audit: 2026-01-15*
*Update as issues are fixed or new ones discovered*
