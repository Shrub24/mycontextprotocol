# Phase 2 Plan 1: Memory store initialization Summary

**Aligned CNPG bootstrap + app secrets with single-namespace stack and operator-managed credentials.**

## Accomplishments

- Switched CNPG bootstrap to template/application SQL, creating mem0/llamaindex/lightrag DBs and installing `vector` + `age` globally in template1
- Consolidated app/data plane releases into `mycontextprotocol` and updated hostnames for same-namespace discovery
- Wired gateway/worker to CNPG app secret and generated a stable `dragonfly-password` secret via Helm lookup
- Added local SOPS secrets stubs to allow helmfile renders without plaintext values

## Files Created/Modified

- `infra/k8s/values/cnpg-cluster/defaults.yaml`
- `infra/k8s/helmfile.yaml`
- `infra/k8s/values/common.yaml`
- `infra/k8s/charts/gateway/templates/deployment.yaml`
- `infra/k8s/charts/gateway/templates/secret.yaml`
- `infra/k8s/charts/gateway/templates/_helpers.tpl`
- `infra/k8s/charts/gateway/templates/configmap.yaml`
- `infra/k8s/charts/worker/templates/scaledjob.yaml`
- `infra/k8s/charts/worker/templates/configmap.yaml`
- `infra/k8s/charts/worker/templates/secret.yaml`
- `infra/k8s/secrets/common.yaml`
- `infra/k8s/secrets/gateway/local.yaml`
- `infra/k8s/secrets/worker/local.yaml`

## Decisions Made

- Keep LlamaIndex wiring in place while keeping the door open to swap storage backends later
- Use CNPG operator-generated `<cluster>-app` secret for internal Postgres credentials
- Use OCI charts for Dragonfly and Dragonfly operator without explicit version pins

## Issues Encountered

- SOPS MAC mismatch blocked helmfile rendering; regenerated encrypted `infra/k8s/secrets/common.yaml` and added local secrets stubs

## Next Step

- Execute Plan 02-02 (app config wiring + Alembic migration cleanup) or proceed to Plan 02-03 for the LightRAG chart wrapper
