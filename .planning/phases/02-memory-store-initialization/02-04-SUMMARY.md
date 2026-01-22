# Phase 2 Plan 4: Memory store initialization Summary

**Unified external secrets handling across charts and moved Dragonfly password ownership into a stack release.**

## Accomplishments

- Added a shared Helm library chart (`mcp-lib`) to standardize external secret wiring
- Centralized external secrets into a single `mycontextprotocol-external` Secret owned by an `external-secrets` release
- Removed legacy per-chart secret templates and file-based prod/local secret stubs
- Added a `dragonfly-secrets` release that owns the `dragonfly-password` Secret used by dragonfly, gateway, and worker

## Files Created/Modified

- `infra/k8s/charts/mcp-lib/Chart.yaml`
- `infra/k8s/charts/mcp-lib/templates/_external_secrets.tpl`
- `infra/k8s/charts/external-secrets/Chart.yaml`
- `infra/k8s/charts/external-secrets/values.yaml`
- `infra/k8s/charts/external-secrets/templates/secret.yaml`
- `infra/k8s/charts/dragonfly-secrets/Chart.yaml`
- `infra/k8s/charts/dragonfly-secrets/templates/secret.yaml`
- `infra/k8s/helmfile.yaml`
- `infra/k8s/secrets/common.yaml`
- `infra/k8s/charts/gateway/values.yaml`
- `infra/k8s/charts/worker/values.yaml`
- `infra/k8s/charts/lightrag/values.yaml`
- `infra/k8s/charts/gateway/templates/deployment.yaml`
- `infra/k8s/charts/worker/templates/scaledjob.yaml`
- `infra/k8s/charts/lightrag/templates/deployment.yaml`

## Decisions Made

- Use a single external secret (`mycontextprotocol-external`) shared by gateway/worker/lightrag
- Keep external secrets provider-agnostic via `externalSecrets` interface and a stack-owned release

## Issues Encountered

- None blocking; helmfile renders validated with the new secret releases

## Next Step

- Decide whether to require `LIGHTRAG_API_KEY` or leave it optional in the external secret
