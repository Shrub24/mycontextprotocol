# Phase 2 Plan 3: Memory store initialization Summary

**Replaced the ad-hoc LightRAG manifest with an in-repo Helm chart and aligned secrets + DB wiring.**

## Accomplishments

- Added a thin LightRAG Helm chart in `infra/k8s/charts/lightrag` using the GHCR image without pinning a tag
- Moved LightRAG to the shared `mycontextprotocol` namespace and removed the standalone manifest
- Wired LightRAG to the CNPG app secret for Postgres credentials and a SOPS-managed `lightrag-secrets`
- Cleaned chart values to rely on shared `values/common.yaml` instead of duplicated host/secret fields

## Files Created/Modified

- `infra/k8s/helmfile.yaml`
- `infra/k8s/charts/lightrag/Chart.yaml`
- `infra/k8s/charts/lightrag/values.yaml`
- `infra/k8s/charts/lightrag/templates/_helpers.tpl`
- `infra/k8s/charts/lightrag/templates/deployment.yaml`
- `infra/k8s/charts/lightrag/templates/service.yaml`
- `infra/k8s/charts/lightrag/templates/pvc.yaml`
- `infra/k8s/values/lightrag/defaults.yaml`
- `infra/k8s/values/lightrag/local.yaml`
- `infra/k8s/values/lightrag/production.yaml`
- `infra/k8s/secrets/templates/lightrag-secrets.yaml`
- `infra/k8s/secrets/profiles/prod/lightrag-secrets.yaml`
- `infra/k8s/charts/gateway/values.yaml`
- `infra/k8s/charts/worker/values.yaml`
- `infra/k8s/charts/gateway/templates/deployment.yaml`
- `infra/k8s/charts/worker/templates/scaledjob.yaml`
- `infra/k8s/manifests/lightrag.yaml`

## Decisions Made

- Use the LightRAG OCI image with no explicit tag pinning
- Keep LightRAG Postgres credentials sourced from `mycontextprotocol-db-app`

## Issues Encountered

- Helm template errors due to legacy chart config; resolved by simplifying chart values and removing redundant config sources

## Next Step

- Advance to the next phase or apply these charts in a live cluster
