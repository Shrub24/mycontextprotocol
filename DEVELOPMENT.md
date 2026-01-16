# Development Guide

**Quick Start:** Run `task --list` to see available tasks.

---

## Philosophy

**Separation of Concerns:**
- **Lefthook (pre-commit):** Fast incremental checks on staged files with fine-grained control
- **Taskfile (CI/manual):** Full codebase checks for comprehensive validation
- Both call CLI tools directly - no circular dependencies

**Why not "task check calls lefthook" or vice versa?**
- Lefthook owns git hook logic (globs, excludes, skip flags, {staged_files})
- Taskfile owns compositional logic (parallel deps, CI entry points)
- Mixing them creates unnecessary coupling

---

## Task Commands

```bash
task format             # Auto-fix formatting (ruff + yamlfmt)
task lint               # Full lint suite (ruff, basedpyright, yamllint, kube/helm)
task typecheck          # Run basedpyright on src + tests
task test               # Run tests

task install            # Install Python dependencies (uv sync)
task dev                # Run FastAPI gateway with hot-reload
task deploy             # Deploy services with helmfile
task deploy:diff        # Preview deployment changes
task clean              # Remove build artifacts and caches
```

---

## Core CLI Commands

### Code Quality
```bash
ruff check --fix src tests       # Lint and auto-fix
ruff format src tests            # Format code
ruff check src tests             # Lint without fixing
basedpyright src tests           # Type check
pytest --cov                     # Run tests with coverage
```

### Database Migrations
```bash
uv run alembic upgrade head                           # Apply migrations
uv run alembic revision --autogenerate -m "message"   # Generate migration
uv run alembic history                                # Show history
```

### Cluster & Kubernetes
```bash
k3d cluster create mcp-local --config k3d/local.yaml  # Create cluster
kubectl logs -f <pod>                                 # Stream logs
stern gateway                                         # Multi-pod logs
kubectl port-forward svc/gateway 8000:80              # Port forward
```

### Python Environment
```bash
uv sync                          # Install dependencies
uv add <package>                 # Add dependency
uv run <command>                 # Run in project environment
```

---

## Common Workflows

### Starting Development
```bash
task install
k3d cluster create mcp-local --config k3d/local.yaml
uv run alembic upgrade head
task dev
```

### Before Committing
```bash
ruff check --fix .
ruff format .
task check                       # Optional - git hooks will run checks
pytest
```

### After Changing Models
```bash
uv run alembic revision --autogenerate -m "describe changes"
uv run alembic upgrade head
```

---

## Git Hooks (Lefthook)

**Pre-commit** runs checks on staged files (fast, incremental):
- `ruff check --fix` → `ruff format` → `ruff check` (Python files only)
- `basedpyright` (Python files only)
- `yamlfmt` + `yamllint` (YAML files only)
- `kube-linter` (infra YAML only)
- `helm lint` (Helm charts only)

**Disabling checks temporarily:**
Edit `lefthook.yml` and add `skip: true` to any command.

**Manual runs:**
```bash
lefthook run pre-commit          # On staged files
lefthook run pre-commit --force  # On all files (ignores globs)
git commit --no-verify           # Skip hooks once
```

---

## Getting Help

- **Task commands:** `task --list`
- **Tool help:** `ruff --help`, `pytest --help`, `kubectl --help`, etc.
- **Documentation:** [Task](https://taskfile.dev/), [uv](https://docs.astral.sh/uv/), [Ruff](https://docs.astral.sh/ruff/), [Alembic](https://alembic.sqlalchemy.org/)
