# Coding Conventions

**Analysis Date:** 2026-01-15

## Naming Patterns

**Files:**
- `snake_case.py` for modules (e.g., `src/mycontextprotocol/worker_llm.py`)
- `test_*.py` for tests (`tests/test_gateway.py`)

**Functions:**
- `snake_case` for functions (`src/mycontextprotocol/worker.py`)

**Variables:**
- `snake_case` for variables
- `UPPER_SNAKE_CASE` for constants

**Types:**
- `PascalCase` for classes and models (`src/mycontextprotocol/config.py`)

## Code Style

**Formatting:**
- Ruff formatter
- Line length 100
- Double quotes for strings

**Linting:**
- Ruff + basedpyright (`pyproject.toml`, `.taskfiles/lint.yml`)

## Import Organization

**Order:**
1. Standard library
2. Third-party packages
3. Local modules

## Error Handling

**Patterns:**
- Raise HTTP errors in FastAPI handlers (`src/mycontextprotocol/gateway.py`)
- Worker logs errors and uses a dead-letter queue (`src/mycontextprotocol/worker.py`)

## Logging

**Framework:**
- Python `logging` module (`src/mycontextprotocol/gateway.py`, `src/mycontextprotocol/worker.py`)

## Comments

**When to Comment:**
- Use docstrings for public functions/classes
- Prefer explaining why, not what

## Function Design

**Size:**
- Keep handlers focused; extract helper functions when logic grows (`src/mycontextprotocol/worker.py`)

**Parameters:**
- Prefer Pydantic models for API inputs (`src/mycontextprotocol/gateway.py`)

## Module Design

**Exports:**
- Explicit exports via `__init__.py` where needed (`src/mycontextprotocol/__init__.py`)

---

*Convention analysis: 2026-01-15*
*Update when patterns change*
