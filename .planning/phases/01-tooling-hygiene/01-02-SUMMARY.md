---
phase: 01-tooling-hygiene
plan: 02
subsystem: infra
tags: [yamlfmt, yamllint, ruff, lix, cachix, nix2container, sops]

# Dependency graph
requires:
  - phase: 01-tooling-hygiene
    provides: lefthook pre-commit ordering
provides:
  - Consistent YAML/format config with normalized CI workflow
  - CI Nix tooling + Cachix integration with SOPS secrets
  - nix2container images with multi-layer caching
affects: [tooling hygiene, CI, image builds]

# Tech tracking
tech-stack:
  added: [lix, cachix, nix2container]
  patterns:
    - CI uses Lix with Cachix + SOPS decrypted token
    - Nix container builds use nix2container with multi-layer images

key-files:
  created:
    - .github/secrets/cachix.sops.json
    - .sops.yaml
  modified:
    - .github/workflows/ci.yml
    - flake.nix
    - nix/images/gateway.nix
    - nix/images/worker.nix
    - nix/images/postgres-age.nix
    - .gitignore

key-decisions:
  - "Use nix2container with maxLayers=100 for OCI images"
  - "Adopt Lix installer + Cachix in CI, with SOPS-managed token"
  - "Use CI-only age key (CI_AGE_KEY) to decrypt Cachix token"

patterns-established:
  - "Nix CI uses extra_nix_config for substituters/keys"

issues-created: []

# Metrics
duration: 25 min
completed: 2026-01-16
---

# Phase 1 Plan 2: Tooling hygiene Summary

**Normalized YAML formatting and CI Nix tooling with Lix, Cachix, and nix2container layering.**

## Performance

- **Duration:** 25 min
- **Started:** 2026-01-16T10:45:41Z
- **Completed:** 2026-01-16T11:10:41Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Aligned formatter/lint configuration to a consistent YAML baseline
- Normalized CI workflow formatting to match yamlfmt/yamllint expectations
- Integrated Lix + Cachix in CI with SOPS-encrypted token and nix2container layering

## Task Commits

Each task was committed atomically:

1. **Task 1: Harmonize formatting configuration** - `e6f47b5` (chore)
2. **Task 2: Normalize YAML formatting baseline** - `fba2d19` (chore)

**Plan metadata:** `ab8cda7` (docs)

## Files Created/Modified
- `.github/workflows/ci.yml` - Lix + Cachix setup and formatting normalization
- `flake.nix` - Cachix substituters + trusted keys
- `nix/images/gateway.nix` - nix2container buildImage with maxLayers
- `nix/images/worker.nix` - nix2container buildImage with maxLayers
- `nix/images/postgres-age.nix` - nix2container buildImage with maxLayers
- `.github/secrets/cachix.sops.json` - SOPS-encrypted Cachix token placeholder
- `.sops.yaml` - CI-only age recipient rule

## Decisions Made
- Use nix2container for OCI images with maxLayers=100
- Standardize CI on Lix + Cachix with SOPS token decryption
- Keep CI age key isolated to CI environment secrets

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- None

## Next Phase Readiness
Ready for 01-03-PLAN.md.

---
*Phase: 01-tooling-hygiene*
*Completed: 2026-01-16*
