# Codebase Structure

**Analysis Date:** 2026-01-15

## Directory Layout

```
mycontextprotocol/
├── .agentinstructions/    # Agent guidance docs
├── .beads/                # Legacy issue tracker (reference only)
├── .github/               # CI workflows
├── .planning/             # GSD planning docs
├── .taskfiles/            # Taskfile task modules
├── alembic/               # DB migrations
├── infra/                 # Kubernetes/Helmfile deployment
├── nix/                   # Nix image definitions
├── src/                   # Python application code
├── tests/                 # Pytest suite
├── flake.nix              # Nix flake
├── pyproject.toml         # Python project config
├── Taskfile.yml           # Task entrypoint
└── uv.lock                # uv dependency lockfile
```

## Directory Purposes

**src/**
- Purpose: Application code for gateway/worker
- Contains: `mycontextprotocol/` package
- Key files: `src/mycontextprotocol/gateway.py`, `src/mycontextprotocol/worker.py`
- Subdirectories: `src/mycontextprotocol/memory/`

**infra/**
- Purpose: Kubernetes manifests and Helm charts
- Contains: `infra/k8s/helmfile.yaml`, charts, values, secrets
- Deployment default: app/data plane in `mycontextprotocol`, operators in system namespaces

**nix/**
- Purpose: Nix image definitions
- Contains: `nix/images/gateway.nix`, `nix/images/worker.nix`

**tests/**
- Purpose: Pytest tests
- Contains: `tests/test_gateway.py`, `tests/test_worker.py`

## Key File Locations

**Entry Points:**
- `src/mycontextprotocol/gateway.py` - FastAPI gateway
- `src/mycontextprotocol/worker.py` - OmniWorker process

**Configuration:**
- `src/mycontextprotocol/config.py` - app settings
- `infra/k8s/.env.example` - infra env template
- `pyproject.toml` - tooling config
- `flake.nix` - dev shell and images

**Core Logic:**
- `src/mycontextprotocol/memory/` - Mem0, LlamaIndex, LightRAG clients
- `src/mycontextprotocol/worker_llm.py` - LLM extraction

**Testing:**
- `tests/` - pytest suite

**Documentation:**
- `README.md` - project overview
- `.agentinstructions/` - agent-specific docs
- `.planning/` - GSD planning docs

## Naming Conventions

**Files:**
- `snake_case.py` for modules
- `test_*.py` for tests in `tests/`

**Directories:**
- `lowercase` for directories

**Special Patterns:**
- `__init__.py` for package exports

## Where to Add New Code

**New Feature:**
- Primary code: `src/mycontextprotocol/`
- Tests: `tests/`
- Config if needed: `src/mycontextprotocol/config.py`

**New Component/Module:**
- Implementation: `src/mycontextprotocol/`
- Types: add to module or `src/mycontextprotocol/models.py`
- Tests: `tests/`

**New Route/Command:**
- Definition: `src/mycontextprotocol/gateway.py`
- Handler: `src/mycontextprotocol/gateway.py`
- Tests: `tests/test_gateway.py`

**Utilities:**
- Shared helpers: `src/mycontextprotocol/`
- Type definitions: `src/mycontextprotocol/models.py`

## Special Directories

**infra/k8s/**
- Purpose: Deployment manifests, Helmfile, charts
- Committed: Yes

**nix/images/**
- Purpose: OCI image builds via Nix
- Committed: Yes

---

*Structure analysis: 2026-01-15*
*Update when directory structure changes*
