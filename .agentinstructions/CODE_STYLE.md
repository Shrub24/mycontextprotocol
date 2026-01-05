# Code Style Guide

This project follows modern Python 3.13+ conventions with minimal, explicit code. The philosophy: **code should be self-documenting; validate once at boundaries; prefer static types over runtime checks.**

## Python

### Language Version
- **Target:** Python 3.13+
- **Key features used:**
  - [PEP 695](https://peps.python.org/pep-0695/): Type parameter syntax
  - [PEP 696](https://peps.python.org/pep-0696/): Type parameter defaults
  - [PEP 705](https://peps.python.org/pep-0705/): TypedDict ReadOnly items
  - [PEP 742](https://peps.python.org/pep-0742/): TypeIs for narrowing

### Toolchain
- **Formatter/Linter:** [Ruff](https://github.com/astral-sh/ruff) (replaces Black, isort, Flake8)
- **Type Checker:** [basedpyright](https://github.com/DetachHead/basedpyright) (fast, LSP-friendly)
- **Validation:** [Pydantic v2](https://github.com/pydantic/pydantic) at I/O boundaries only

Configuration lives in `pyproject.toml`.

### Type Hints
**Required** on all public APIs and function signatures. Use modern syntax:

```python
# ✅ Modern (PEP 695)
def process[T](items: list[T]) -> list[T]: ...

# ❌ Old
from typing import TypeVar, List
T = TypeVar('T')
def process(items: List[T]) -> List[T]: ...
```

**TypedDict for structured data:**
```python
from typing import TypedDict, ReadOnly

class Memory(TypedDict):
    id: ReadOnly[str]  # PEP 705
    content: str
    source: str
```

**Protocols for structural typing** (use sparingly):
```python
from typing import Protocol

class Embeddable(Protocol):
    def embed(self) -> list[float]: ...
```

### Validation
**Validate at I/O boundaries only.** Use Pydantic v2 for external inputs:

```python
from pydantic import BaseModel, field_validator

class InboxRequest(BaseModel):
    content: str
    source: str
    
    @field_validator('content')
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('content cannot be empty')
        return v
```

**Internal functions assume valid inputs** (enforced by types):
```python
# ✅ No validation needed - types enforce correctness
def store_memory(memory: Memory) -> None:
    db.insert(memory)

# ❌ Don't repeat validation internally
def store_memory(memory: Memory) -> None:
    if not memory['content']:  # Redundant!
        raise ValueError(...)
    db.insert(memory)
```

### Error Handling
- **Explicit exceptions at boundaries:** Catch and handle at API/queue/file boundaries
- **Let it crash internally:** Don't catch exceptions just to re-raise them
- **Use standard exceptions:** `ValueError`, `TypeError`, `KeyError` over custom ones

```python
# ✅ Handle at boundary
def add_memory_handler(request: dict) -> dict:
    try:
        validated = InboxRequest.model_validate(request)
        return process_memory(validated)
    except ValidationError as e:
        return {"error": str(e)}

# ✅ Internal code - no defensive checks
def process_memory(req: InboxRequest) -> dict:
    memory = create_memory(req.content, req.source)
    store_memory(memory)
    return {"id": memory['id']}
```

### Naming
- **Functions/variables:** `snake_case`
- **Classes:** `PascalCase`
- **Constants:** `UPPER_SNAKE_CASE`
- **Private:** `_leading_underscore`
- **Be explicit:** `get_user_by_id()` not `get_user()`

### Comments & Docstrings
**Prefer clear code over comments.** Only document:
- Public APIs (brief docstrings)
- Non-obvious "why" (not "what")
- Complex algorithms

```python
# ✅ Good - documents "why"
def retry_with_backoff(func, max_attempts: int = 3) -> Any:
    """Retry with exponential backoff for transient failures."""
    ...

# ❌ Bad - restates the obvious
def get_memory(id: str) -> Memory:
    """Gets a memory by ID."""  # Don't do this
    ...
```

**Docstring format:** Google style, minimal:
```python
def embed_document(content: str, model: str = "text-embedding-3-small") -> list[float]:
    """Generate embeddings for document content.
    
    Args:
        content: Text to embed
        model: OpenAI model name
        
    Returns:
        768-dimensional embedding vector
    """
```

### Principles
- **YAGNI:** Don't add features until needed
- **DRY:** Extract repeated logic to functions/modules
- **No magic numbers:** Use named constants (except in tests/placeholders)
- **Explicit over implicit:** `return None` not just `return`
- **One responsibility:** Functions do one thing

## YAML

### Style
- **Indentation:** 2 spaces (matches Kubernetes conventions)
- **Quotes:** Use for strings with special chars, avoid otherwise
- **Multiline:** Use `|` for long text, `>` for folded

```yaml
# ✅ Good
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  database_url: postgresql://localhost/db
  long_text: |
    This is a long
    multiline string
```

### Linting
Use `yamllint` (config in `.yamllint`). Key rules:
- No trailing spaces
- Consistent indentation
- Line length 120 chars

### Secrets
**Never commit secrets.** Use placeholders:
```yaml
# ✅ Good - reference
password: ${POSTGRES_PASSWORD}

# ❌ Bad - literal
password: "super-secret-123"
```

## Nix

### Flake Structure
- Keep `flake.nix` minimal and readable
- Pin dependencies via `flake.lock` (commit it)
- Document non-obvious derivations

### When to Update Lock
```bash
# After adding/removing packages
nix flake update

# Target specific input
nix flake lock --update-input nixpkgs
```

### Shell Hook
Keep it brief - show versions and quick commands only.

## Repository

### File Organization
```
mycontextprotocol/
├── functions/          # OpenFaaS Python functions
├── infra/             # IaC (K8s, OpenTofu)
├── scripts/           # Helper scripts
├── docs/              # Documentation
└── .agentinstructions/ # Architecture, agent workflows
```

### .editorconfig
Respect the project's `.editorconfig` - do not reformat files unnecessarily.

### Git
- **Commits:** Imperative mood ("Add feature" not "Added feature")
- **Scope:** One logical change per commit
- **No secrets:** Use `.gitignore`, pre-commit hooks

### Ignored Files
See `.gitignore`. Key patterns:
- `.direnv/` - direnv cache
- `result*` - Nix build outputs
- `*.secret.yaml` - Secret configs
- `__pycache__/`, `*.pyc` - Python artifacts
- `.terraform/`, `*.tfstate` - IaC state

## Tools Configuration

All tool config lives in:
- `pyproject.toml` - Python tools (ruff, basedpyright)
- `.yamllint` - YAML linting
- `.editorconfig` - Editor settings
- `flake.nix` - Dev environment

## CI/CD

Pipeline order (when implemented):
1. `ruff format --check` (formatting)
2. `ruff check` (linting)
3. `basedpyright` (type checking)
4. `pytest` (tests)

Pin tool versions in CI to match `flake.nix`.

## References

- [Python 3.13 What's New](https://docs.python.org/3.13/whatsnew/3.13.html)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Pydantic v2 Docs](https://docs.pydantic.dev/latest/)
- [PEP 695 (Type Parameters)](https://peps.python.org/pep-0695/)
- [PEP 696 (Type Defaults)](https://peps.python.org/pep-0696/)
