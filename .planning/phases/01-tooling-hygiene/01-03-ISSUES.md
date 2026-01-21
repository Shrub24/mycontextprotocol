# UAT Issues: Phase 1 Plan 3

**Tested:** 2026-01-21
**Source:** .planning/phases/01-tooling-hygiene/01-03-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

### UAT-001: `task typecheck` command missing

**Discovered:** 2026-01-21
**Phase/Plan:** 01-03
**Severity:** Major
**Feature:** Taskfile typecheck command
**Description:** `task typecheck` is not available; task listing shows only `typecheck:typecheck:*` entries. Running `task typecheck` fails with "Task \"typecheck\" does not exist".
**Expected:** `task typecheck` should exist (consistent with other tasks) and run basedpyright over src + tests.
**Actual:** The only entries are namespaced (`typecheck:typecheck:*`), so `task typecheck` fails.
**Repro:**
1. Run `task --list`
2. Observe `typecheck:typecheck:*` entries but no `typecheck`
3. Run `task typecheck` → "Task \"typecheck\" does not exist"

## Resolved Issues

[None yet]

---

*Phase: 01-tooling-hygiene*
*Plan: 03*
*Tested: 2026-01-21*
