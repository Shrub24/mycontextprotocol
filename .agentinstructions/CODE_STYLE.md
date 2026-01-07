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

**Minimal commenting philosophy:**
- Code should be self-documenting through clear names and structure
- Only comment when information CANNOT be expressed in code
- Prefer language-standard docstrings over inline comments
- No markdown-style formatting in code comments (no headers, bullets, etc.)

**When to comment:**
- ✅ Public API docstrings (standard format for language)
- ✅ Non-obvious "why" that affects correctness
- ✅ Complex algorithms (performance tricks, mathematical formulas)
- ✅ Security-sensitive code (explain threat model)
- ✅ Workarounds for external bugs (link to issue tracker)

**When NOT to comment:**
- ❌ Describing what code does (code should be obvious)
- ❌ Section dividers in normal code files (use modules/functions instead)
- ❌ Structured markdown-style comments (no headers, lists)
- ❌ Default values or placeholder configs (use TODO or searchable syntax)

```python
# ✅ Good - explains non-obvious "why"
def retry_with_backoff(func, max_attempts: int = 3) -> Any:
    """Retry with exponential backoff for transient failures."""
    # Use exponential backoff to avoid thundering herd on service recovery
    ...

# ❌ Bad - restates what code does
def get_memory(id: str) -> Memory:
    """Gets a memory by ID."""  # Obvious from function name
    ...

# ❌ Bad - markdown-style section divider
# ============================================================
# Memory Management Functions
# ============================================================
def get_memory(id: str) -> Memory:
    ...

# ✅ Good - use module structure instead
# File: memory/retrieval.py (separation via filesystem)
def get_memory(id: str) -> Memory:
    ...
```

**Docstring format:** Language-standard only (Google style for Python), minimal:
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

**Exceptions for structured comments:**
- Dockerfiles: Stage comments like `# Build stage` / `# Runtime stage` are idiomatic
- Long files: Major section dividers for clarity (use sparingly, only when truly needed)
- YAML/Helm: Infrastructure comments explaining purpose (matches K8s conventions)

### Configuration & Placeholders

**Required configuration values:**
```python
# ❌ Bad - arbitrary placeholder
database_url = "postgresql://localhost/db"

# ❌ Bad - generic placeholder without context
api_key = "your-api-key-here"

# ✅ Good - no default, required from env
class Config(BaseSettings):
    postgres_host: str
    postgres_password: str
    openai_api_key: str

# ✅ Good - TODO for required secret
# In YAML:
# TODO: OPENAI_API_KEY must be set via secrets
```

**Optional parameters:**
```yaml
# YAML/Helm values - only set if we need to configure it
# ❌ Bad - duplicating chart default
service:
  type: ClusterIP  # Chart already defaults to this
  port: 8080       # Chart already defaults to this

# ✅ Good - we need to configure these
replicas: 3  # Will vary by environment (local=1, prod=3+)
resources:
  limits:
    cpu: 2000m
    memory: 4Gi
```

```python
# Pydantic Settings - set our internal defaults
# ✅ Good - our infrastructure config
class Mem0Settings(BaseSettings):
    postgres_host: str = "postgresql-cluster-rw.database.svc.cluster.local"
    postgres_port: int = 5432
    postgres_database: str = "mem0"
    postgres_password: str  # No default - required secret

# Pydantic IO models - default only if sensible
# ✅ Good - no default for strictly required fields
class QueryRequest(BaseModel):
    query: str = Field(..., description="Search query")  # Required
    user_id: str = Field(..., description="User ID")     # Required

# ✅ Good - default for fields with sensible defaults
class QueryRequest(BaseModel):
    query: str = Field(...)
    limit: int = Field(10, description="Max results", ge=1, le=100)  # Sensible default
    mode: Literal["fast", "accurate"] = Field("fast")  # Sensible default
```

**Rule:**
- **YAML values**: Only set if we need to configure/tune it (replicas, resources, custom settings)
- **Pydantic Settings**: Set our internal defaults (infra hostnames, ports, databases)
- **Pydantic IO models**: Only default if field has a sensible default that works for most cases

### Validation

**Pydantic models for IO - add Field() annotations with descriptions:**

Models used for API request/response (especially agentic IO) need proper schema documentation:

```python
# ✅ Good - IO model with Field() annotations
class QueryRequest(BaseModel):
    """Semantic search query for document store."""
    
    query: str = Field(..., description="Natural language search query")
    user_id: str = Field(..., description="User identifier")
    limit: int = Field(10, description="Max results", ge=1, le=100)
    mode: Literal["fast", "accurate"] = Field("fast", description="Search mode")

# ❌ Bad - no Field() annotations, no descriptions
class QueryRequest(BaseModel):
    query: str
    user_id: str
    limit: int = 10
    mode: Literal["fast", "accurate"] = "fast"
```

**Model docstrings for IO models:**
- Add class docstrings for all API request/response models
- These become part of OpenAPI schema for agents/LLMs
- Keep brief - one line describing the model's purpose

**Internal models can skip Field() if obvious:**
```python
# Internal data structures - Field() optional
class Memory(TypedDict):
    id: str
    content: str
    source: str
```

**Use YAML/JSON schemas where available:**
- Check for official schemas first (CRDs, OpenAPI specs, etc.)
- If no official schema exists, document this and create custom validation

```python
# For Kubernetes manifests - use kubectl validation or official CRD schemas

# For custom configs - use Pydantic
from pydantic import BaseModel, Field

class DatabaseConfig(BaseModel):
    host: str = Field(..., description="PostgreSQL host")
    port: int = Field(5432, ge=1, le=65535)
    database: str = Field(..., min_length=1)
```

### Principles
- **YAGNI:** Don't add features until needed
- **DRY:** Extract repeated logic to functions/modules
- **No magic numbers:** Use named constants (no arbitrary literals)
- **Explicit over implicit:** `return None` not just `return`
- **One responsibility:** Functions do one thing
- **Follow existing patterns:** Consistency over personal preference (see DEVELOPMENT.md)

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

### Secrets & Required Values
**Never commit secrets.** Use environment variable references or TODO tags:
```yaml
# ✅ Good - environment variable reference
password: ${POSTGRES_PASSWORD}

# ✅ Good - TODO tag (searchable)
# TODO: Set password via secret
password: ""

# ❌ Bad - arbitrary placeholder
password: "changeme"

# ❌ Bad - fake/example secret
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
