# Testing Patterns

**Analysis Date:** 2026-01-15

## Test Framework

**Runner:**
- Pytest with pytest-asyncio (`pyproject.toml`)

**Assertion Library:**
- Pytest built-in assertions

**Run Commands:**
```bash
task test           # Run all tests
task test:cov       # Run tests with coverage
uv run pytest tests # Direct pytest invocation
```

## Test File Organization

**Location:**
- `tests/` directory

**Naming:**
- `test_*.py` (e.g., `tests/test_gateway.py`)

## Test Structure

**Suite Organization:**
- Uses pytest functions with fixtures (`tests/conftest.py`)

**Patterns:**
- Async tests use `pytest.mark.asyncio`
- Mocks via `unittest.mock` (`tests/test_worker.py`)

## Mocking

**Framework:**
- `unittest.mock` (patch, Mock, AsyncMock)

**What to Mock:**
- External services (Redis/Dragonfly, LightRAG, Ollama)
- Database clients

## Coverage

**Requirements:**
- 70% minimum enforced (`.taskfiles/test.yml`)

**Configuration:**
- `pytest-cov` via Taskfile and `pyproject.toml`

**View Coverage:**
```bash
task test:cov
```

## Test Types

**Unit Tests:**
- Gateway and worker behaviors in isolation (`tests/test_gateway.py`, `tests/test_worker.py`)

**Integration Tests:**
- Not detected

**E2E Tests:**
- Not detected

---

*Testing analysis: 2026-01-15*
*Update when test patterns change*
