# Project State

**Last Updated:** 2026-01-15

## Planning System

This repo now uses **GSD planning docs** instead of beads. Current backlog and priorities live here and in `.planning/PLAN.md` (if present).

## Active Work

**In Progress:**
- `mycontextprotocol-4r2` - Create Nix-based container images for gateway and worker (legacy beads issue; status tracked here now)

## Backlog (Pending)

**Priority 1-2:**
- `mycontextprotocol-j49` - Add Apache AGE extension to CloudNativePG
- `mycontextprotocol-h6w` - Implement explicit memory access endpoints (LlamaIndex + LightRAG tools)
- `mycontextprotocol-wqr` - Add Helm chart for gateway/worker deployments
- `mycontextprotocol-tsv` - Test end-to-end local deployment
- `mycontextprotocol-6hk` - Add k9s and stern to dev tooling

**Priority 3:**
- `mycontextprotocol-8km` - Fix existing yamllint issues in codebase
- `mycontextprotocol-9u4` - Setup Dependabot for dependency updates
- `mycontextprotocol-ajy` - Add MinIO for file storage (Phase 2/3)
- `mycontextprotocol-b8y` - Implement Dragonfly context cache for Mem0 results (Phase 2/3)
- `mycontextprotocol-dfy` - Implement query routing strategy (Phase 2/3)

**Priority 4:**
- `mycontextprotocol-7mm` - Create docs skeleton (getting-started, deployment)
- `mycontextprotocol-98y` - Setup CI/CD pipeline for automated deployment
- `mycontextprotocol-d75` - Setup OpenTofu IaC for cloud infrastructure
- `mycontextprotocol-x6k` - Setup OpenTelemetry observability stack (SigNoz + Langfuse)

## Notes

- Legacy beads issues live in `.beads/issues.jsonl` for reference only.
- Update this file when backlog changes or priorities shift.
