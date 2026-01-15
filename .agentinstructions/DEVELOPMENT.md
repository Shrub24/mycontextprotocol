# Development Workflow for Agents

This document captures agent-focused development guidance. Project planning and architecture live in GSD planning docs under `.planning/`.

## Planning Sources

- Backlog and priorities: `.planning/STATE.md`
- Active execution plan: `.planning/PLAN.md`
- Codebase map (architecture/structure/testing/integrations): `.planning/codebase/*.md`

## Core Principles

1. **Follow the plan** — execute tasks from `.planning/PLAN.md`.
2. **Minimal changes** — do only what is required.
3. **Validate at boundaries** — types for internal correctness, explicit validation at I/O boundaries.
4. **Ask, don’t guess** — clarify ambiguous requirements with the user.
5. **Report blockers** — return with the problem and options.

## Implementation Standards

- Use `.agentinstructions/CODE_STYLE.md` for code conventions.
- Match existing patterns (imports, naming, error handling).
- Avoid large refactors unless explicitly requested.

## Quality Checks

- `task format` — formatting
- `task lint` — lint checks
- `task typecheck` — type checks
- `task test:cov` — tests with coverage

Run the smallest relevant checks unless the user requests full validation.

## Git Workflow

- Do **not** run `git add`, `git commit`, or `git push` unless explicitly instructed by the user.
- Provide a concise summary of changes for the user to review.

## References

- Architecture overview: `.planning/codebase/ARCHITECTURE.md`
- System structure: `.planning/codebase/STRUCTURE.md`
- Testing patterns: `.planning/codebase/TESTING.md`
- External integrations: `.planning/codebase/INTEGRATIONS.md`
