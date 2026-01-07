# Development Workflow for Agents

This document guides AI agents (and human contributors) through the development process for mycontextprotocol.

## Philosophy

**Agents are implementers, not designers.** Follow the plan; ask when unclear; return to user when blocked.

### Core Principles
1. **Follow the plan** - Execute tasks from `bd` issues and project plans
2. **Minimal changes** - Only change what's required (YAGNI)
3. **Validate at boundaries** - Use types for internal correctness, validate external inputs only
4. **Ask, don't guess** - When unclear, ask the user before deviating
5. **Report blockers** - Return to user with problem + solutions when stuck

## Project Context

### Repository Scope

**THIS REPOSITORY IS FOR PART A ONLY: MyContextProtocol (The Memory Backend)**

This repo contains:
- Memory-as-a-Service API (FastAPI gateway)
- KEDA-scaled workers for batch processing
- Mem0 (library) integration for episodic/subjective memory
- LlamaIndex integration for semantic search and knowledge graph
- Infrastructure (Postgres, Dragonfly, KEDA)
- Helm charts and deployment manifests

**Part B (Personal AI Stack) is context ONLY:**
- OpenWebUI, LiteLLM, Copilot Proxy are mentioned for integration context
- They are NOT in this repo
- They consume MyContextProtocol's API endpoints
- References to Part B explain HOW this memory backend will be used

**When working on issues:**
- Focus exclusively on the memory backend (Part A)
- Part B references are for understanding integration patterns
- Do NOT implement OpenWebUI, LiteLLM, or frontend components here

### Key Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| **KEDA + Containers** (not OpenFaaS) | No framework lock-in, standard Kubernetes primitives |
| **Dragonfly** (not Redis/NATS) | Redis-compatible, lower memory, better ARM64 perf, dual-role (queue + cache) |
| **CloudNativePG** (not Bitnami) | Declarative backups, automatic failover, better operators |
| **Mem0 as library** (not API server) | Avoids ARM64 blocker, direct Python access |
| **Python for workers** | Mem0/LlamaIndex native, workers are IO-bound not CPU-bound |

### State vs Tools Pattern

**State (Mem0)** - Automatic middleware:
- Called every request via OpenWebUI Filter
- Returns user context for System Prompt injection
- Target latency: <100ms (can cache in Phase 2/3)
- Endpoint: `POST /context/state`

**Tools (LlamaIndex)** - On-demand retrieval:
- LLM decides when to call
- Returns relevant documents/facts from knowledge base
- Target latency: <500ms
- Endpoint: `POST /context/query`

## Workflow

### 1. Check Work Queue
```bash
bd ready
```

Shows available issues prioritized P0 (critical) → P4 (low).

### 2. Claim Work
```bash
bd update <issue-id> --status in_progress
```

Only one issue `in_progress` at a time.

### 3. Understand Requirements
- Read issue description
- Check referenced docs (ARCHITECTURE.md, CODE_STYLE.md)
- If unclear: **ASK USER** before proceeding

### 4. Implement
Follow CODE_STYLE.md:
- Minimal, idiomatic code
- Types enforce correctness (no redundant validation)
- Clear names over comments
- Validate once at I/O boundaries

### 5. Verify
- Check types: `basedpyright <file>`
- Check style: `ruff check <file>`
- Test manually if no automated tests exist yet
- For IO models: Verify Field() annotations with descriptions are present

### 6. Complete
```bash
bd close <issue-id> --comment "Brief description of what was done"
```

## Agent Delegation

**Agents should delegate research and exploration tasks to specialized child agents rather than using direct tool calls.**

### Available Agents

| Agent | Model/Capability | Use Case |
|-------|------------------|----------|
| **explore** | Fast codebase exploration | Find implementations, patterns, structure. Contextual grep for "where is X?" |
| **librarian** | Multi-repo + docs | Search external docs, GitHub repos, API references, OSS examples |
| **oracle** | Deep reasoning (expensive) | Architecture decisions, code review, strategy, complex debugging after 2+ failures |
| **frontend-ui-ux-engineer** | UI/UX specialist | Visual/styling changes ONLY (colors, layout, animations). Not logic. |
| **document-writer** | Technical writing | README, API docs, architecture docs, guides |
| **multimodal-looker** | Visual analysis | PDFs, images, diagrams - extracts info beyond raw text |

### When to Use Child Agents

| Task Type | Agent | Pattern |
|-----------|-------|---------|
| **Codebase search** | `explore` | Multiple search angles, unfamiliar modules |
| **External docs** | `librarian` | Library APIs, best practices, OSS examples |
| **Architecture** | `oracle` | Multi-system tradeoffs, design decisions |
| **Code review** | `oracle` | After completing significant implementation |
| **Hard debugging** | `oracle` | After 2+ failed fix attempts |
| **Frontend visuals** | `frontend-ui-ux-engineer` | Styling, layout, animations (delegate if ANY visual keywords) |
| **Documentation** | `document-writer` | Technical writing tasks |
| **Media analysis** | `multimodal-looker` | Need analyzed/extracted data from PDFs/images |

### Pattern: Parallel Background Tasks

**Default behavior:** Fire multiple agents in parallel, continue working while they run.

```python
# CORRECT: Parallel exploration
background_task(agent="explore", prompt="Find all authentication implementations in the codebase")
background_task(agent="explore", prompt="Locate error handling patterns used in services/")
background_task(agent="librarian", prompt="Find best practices for KEDA ScaledJobs with Python")

# Continue immediate work - system notifies when agents complete
# Later: background_output(task_id="...") to retrieve results
```

```python
# WRONG: Direct tool calls for research
grep_pattern = "authentication"  # Don't do this for exploratory work
read_file("/path/to/file")       # Use explore agent instead
```

### When NOT to Use Child Agents

- **Known file location** - Just use `read` directly
- **Single grep pattern** - Direct tool faster than agent overhead  
- **Trivial searches** - "Find the README" doesn't need an agent

### Collecting Results

```bash
# System notifies you when background tasks complete
# Retrieve results when needed:
background_output(task_id="task_abc123")

# Before final answer, always cancel remaining tasks:
background_cancel(all=true)
```

## Pattern Consistency

**Core principle:** Always follow existing patterns unless explicitly changing them. Consistency matters more than personal preference.

### Detecting Pattern Inconsistencies

When working on a file or module, actively look for:
- **Naming conventions** - Do functions use `get_x()` or `fetch_x()`? Stick with what exists.
- **Import organization** - Grouped by stdlib/third-party/local? Alphabetized? Match it.
- **Error handling** - Does code raise exceptions or return `None`? Be consistent.
- **Type annotations** - Are they present? Use the same style (PEP 695 vs old-style).
- **Docstring style** - Google style? NumPy style? Match what's there.
- **Configuration patterns** - Environment variables? Pydantic Settings? BaseModel? Follow existing.

### When Patterns Conflict

**If you find multiple conflicting patterns in the codebase:**

1. **First, verify it's actually inconsistent:**
   - Different patterns may serve different purposes (intentional design)
   - Migration might be in progress (old code vs new code)
   - You might be comparing unrelated subsystems

2. **If genuinely inconsistent, assess relevance and impact:**
   - **Minor/cosmetic inconsistency (2-3 occurrences)** → Infer the "winning" pattern:
     - Most recent code (check git blame if needed)
     - Pattern that matches CODE_STYLE.md
     - Pattern used in related/surrounding code
   - **Significant inconsistency OR affects correctness/maintainability** → **FLAG AND STOP**
   - Use judgment: cosmetic issues (proceed), architectural issues (stop)

3. **Document your reasoning:**
   ```
   PATTERN INCONSISTENCY DETECTED: Error handling in services/
   
   Pattern A (3 files): Raise HTTPException directly
   Pattern B (2 files): Return dict with {"error": ...}
   Pattern C (1 file): Custom exception classes
   
   Recommendation: Pattern A (most common, matches FastAPI conventions)
   
   Proceeding with Pattern A unless you prefer differently?
   ```

### When Changing Patterns

**Never change existing patterns without explicit user approval.**

If you believe a pattern should change:
1. **Stop** - Don't make the change yet
2. **Document** the current pattern and why it's problematic
3. **Propose** the new pattern with concrete benefits
4. **Ask** user for approval before proceeding

Example:
```
Current pattern uses `as any` type suppressions in 5 places.
This violates CODE_STYLE.md and hides type errors.

Proposed: Properly type these with Protocol or TypedDict.
Effort: ~30 minutes to fix all occurrences.

Should I refactor these or work around them for now?
```

### Pattern Consistency Checklist

Before committing code, verify:
- [ ] Naming matches surrounding code
- [ ] Import style matches file conventions
- [ ] Error handling matches module patterns
- [ ] Type annotations match codebase style
- [ ] Docstrings match existing format
- [ ] No arbitrary pattern changes introduced

**Remember:** Consistency > "better" way. Follow what exists unless user approves change.

## Decision Points

### When to Ask User
- Unclear requirements or ambiguous issue description
- Multiple valid implementations with significant tradeoffs
- Need to deviate from the plan due to unforeseen constraints
- Discover architectural issues that affect other components

### When to Proceed
- Single clear implementation path
- Minor style/naming decisions within CODE_STYLE.md guidelines
- Implementation details not specified in requirements

### When Blocked
**Stop and report:**
1. **Problem:** Clear description of the blocker
2. **Context:** What you tried, what failed
3. **Options:** 2-3 potential solutions with tradeoffs
4. **Recommendation:** Your suggested path forward

Example:
```
BLOCKED: Cannot deploy Mem0 API server - image doesn't support ARM64

Context:
- Attempted to deploy mem0ai/mem0:latest
- Error: "no matching manifest for linux/arm64"

Options:
1. Use x86_64 image with QEMU emulation (slow, works)
2. Build ARM64 image from source (requires maintaining build)
3. Use Mem0 Python library embedded in worker (more control, no server needed)

Recommendation: Option 3 - gives us control, avoids emulation overhead, aligns with
our "library over service" preference for Python-native components.

Should I proceed with Option 3?
```

## Technology Stack Reference

### Development Tools

| Tool | Purpose | Command |
|------|---------|---------|
| **uv** | Python package manager | `uv sync`, `uv add <package>` |
| **ruff** | Linter + formatter | `ruff check`, `ruff format` |
| **basedpyright** | Type checker | `basedpyright src/` |
| **lefthook** | Git hooks | Auto-runs on commit/push |
| **Taskfile** | Task automation | `task check`, `task db:upgrade` |
| **Alembic** | DB migrations | `task db:autogenerate`, `task db:upgrade` |
| **k9s** | K8s TUI | `k9s` |
| **stern** | Log streaming | `stern <pod-pattern>` |

### Core Services

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Database** | CloudNativePG (Postgres 16 + pgvector) | All persistent data (Mem0 tables, vectors, graph) |
| **Queue + Cache** | Dragonfly | Ingest queue + future user context cache |
| **Scaling** | KEDA | Scale workers based on queue depth / cron |
| **Gateway** | FastAPI (Python 3.13) | `/ingest`, `/context/state`, `/context/query` endpoints |
| **Worker** | Python 3.13 container | Omni-Worker: LLM extraction → Mem0 + LlamaIndex writes |

### Python Libraries (Worker)

- **Mem0**: Episodic memory, user facts, entity resolution
- **LlamaIndex**: Semantic search, property graph, document indexing
- **instructor**: LLM output validation with Pydantic
- **psycopg[binary]**: Postgres driver with C extensions
- **redis**: Dragonfly client (Redis-compatible)
- **fastapi**: API gateway framework
- **pydantic**: Data validation (v2)

### Infrastructure

- **Production**: Oracle Cloud ARM (4 OCPU, 24GB RAM)
- **Local**: k3d (K3s in Docker)
- **Deployment**: Helmfile for orchestration
- **Ingress**: Cloudflare Tunnel (prod) / NodePort (local)
- **Python**: 3.13 (NOT 3.12 - user specified)

## Common Patterns

### Working with KEDA ScaledJobs

KEDA scales Jobs (not Deployments) based on external metrics.

```yaml
# Example ScaledJob for Omni-Worker
apiVersion: keda.sh/v1alpha1
kind: ScaledJob
metadata:
  name: omni-worker
spec:
  jobTargetRef:
    template:
      spec:
        containers:
        - name: worker
          image: mycontextprotocol/omni-worker:latest
          env:
          - name: POSTGRES_HOST
            value: postgres-cluster-rw.database.svc.cluster.local
  triggers:
  - type: redis  # Dragonfly is Redis-compatible
    metadata:
      address: dragonfly:6379
      listName: ingest-queue
      listLength: "10"  # Batch when >= 10 messages
```

### Working with Mem0 Library

Mem0 is used as an **embedded library**, not an API server.

```python
from mem0 import Memory

# Initialize (in worker)
mem0 = Memory.from_config({
    "graph_store": {
        "provider": "postgres",
        "config": {
            "host": os.getenv("POSTGRES_HOST"),
            "port": 5432,
            "database": "postgres",
            "user": "postgres",
            "password": os.getenv("POSTGRES_PASSWORD")
        }
    }
})

# Add memory (subjective facts)
mem0.add(
    messages=[{"role": "user", "content": "I prefer concise answers"}],
    user_id="alice"
)

# Search memories
results = mem0.search("user preferences", user_id="alice")
```

### Working with LlamaIndex PropertyGraph

LlamaIndex stores documents + graph in Postgres.

```python
from llama_index.core import PropertyGraphIndex
from llama_index.graph_stores.postgres import PostgresPropertyGraphStore

# Initialize
graph_store = PostgresPropertyGraphStore(
    host=os.getenv("POSTGRES_HOST"),
    port=5432,
    database="postgres",
    user="postgres",
    password=os.getenv("POSTGRES_PASSWORD")
)

index = PropertyGraphIndex.from_graph_store(graph_store)

# Insert document (objective knowledge)
index.insert(
    text="KEDA is a Kubernetes event-driven autoscaler",
    metadata={"source": "documentation", "date": "2024-01-01"}
)

# Query
results = index.query("What is KEDA?")
```

### Working with Dragonfly Queue

Dragonfly is Redis-compatible.

```python
import redis

# Connect
r = redis.Redis(host='dragonfly', port=6379, decode_responses=True)

# Producer (FastAPI gateway)
r.lpush('ingest-queue', json.dumps({
    "inbox_id": str(uuid.uuid4()),
    "content": content,
    "source": source
}))

# Consumer (Worker)
while True:
    # Blocking pop with 30s timeout
    result = r.brpop('ingest-queue', timeout=30)
    if result:
        queue_name, message = result
        data = json.loads(message)
        process(data)
```

### Database Migrations (Alembic)

**Source of Truth**: SQLAlchemy models in `src/mycontextprotocol/models.py`

**Workflow**:
```bash
# 1. Modify SQLAlchemy models (add/change tables, columns)
# Example: Add new column to Inbox model in src/mycontextprotocol/models.py

# 2. Generate migration (Alembic inspects models vs DB)
task db:autogenerate -- "add processed_at column to inbox"

# 3. Review generated migration
# Check alembic/versions/xxxx_add_processed_at_column_to_inbox.py

# 4. Apply migration
task db:upgrade

# If needed: rollback
task db:downgrade
```

**Example Model**:
```python
# src/mycontextprotocol/models.py
from sqlalchemy import Column, String, TIMESTAMP, Boolean, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Inbox(Base):
    __tablename__ = "inbox"
    
    id = Column(UUID, primary_key=True, server_default=text("gen_random_uuid()"))
    content = Column(String, nullable=False)
    source = Column(String(100))
    processed = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=text("now()"))
    processed_at = Column(TIMESTAMP)  # New column
```

**Benefits**:
- Models are source of truth (code-first)
- Autogenerate detects schema drift
- Version-controlled migrations
- Declarative schema management

### Adding New API Endpoints

FastAPI follows this pattern:

```python
# In services/gateway/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class IngestRequest(BaseModel):
    content: str
    source: str
    metadata: dict = {}

@app.post("/ingest")
async def ingest(request: IngestRequest):
    # Validate
    if not request.content:
        raise HTTPException(400, "Content required")
    
    # Queue for processing
    inbox_id = str(uuid.uuid4())
    dragonfly.lpush('ingest-queue', json.dumps({
        "inbox_id": inbox_id,
        "content": request.content,
        "source": request.source,
        "metadata": request.metadata
    }))
    
    return {"id": inbox_id, "status": "queued"}
```

### Building Containers for ARM64

All images must support `linux/arm64` for Oracle Cloud.

```bash
# Build multi-arch
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t mycontextprotocol/gateway:latest \
  --push \
  .

# Or build ARM64 only (for Oracle Cloud)
docker buildx build \
  --platform linux/arm64 \
  -t mycontextprotocol/gateway:latest \
  --push \
  .
```

## Code Quality

### Pydantic Models for IO

**API request/response models need proper Field() annotations:**

```python
# ✅ Good - IO model with schema documentation
class QueryRequest(BaseModel):
    """Semantic search query for document store."""
    
    query: str = Field(..., description="Natural language search query")
    user_id: str = Field(..., description="User identifier")
    limit: int = Field(10, description="Max results", ge=1, le=100)

# ❌ Bad - missing Field() annotations
class QueryRequest(BaseModel):
    query: str
    user_id: str
    limit: int = 10
```

**Why this matters:**
- Field descriptions become OpenAPI schema documentation
- Agents/LLMs use this to understand how to call the API
- Validation constraints (ge, le, min_length) enforce correctness at boundaries

**Rules:**
- **Always** add Field() with descriptions for API models (request/response)
- **Always** add model docstring (one line describing purpose)
- **Optional** for internal data structures (TypedDict, etc.)
- Only default if field has sensible default that works for most cases

### Development Workflow

```bash
# Enter dev environment
nix develop

# Install/sync dependencies
uv sync

# Run all checks before committing
task check          # Runs: format + lint + typecheck

# Individual checks
task format         # Auto-format with ruff
task lint           # Check code quality
task typecheck      # Verify types with basedpyright
```

### Git Hooks (Automatic via Lefthook)

**Pre-commit** (runs automatically on `git commit`):
- `ruff format --check` - Verify formatting
- `ruff check` - Lint staged files
- `basedpyright` - Type check staged files

**Pre-push** (runs automatically on `git push`):
- `task check` - Full validation

**Bypass (if needed)**:
```bash
git commit --no-verify  # Skip pre-commit hooks (use sparingly)
```

### Before Committing
1. **All checks pass:** `task check` exits 0
2. **No secrets:** Check for API keys, passwords in code
3. **Respects .editorconfig:** Don't reformat unrelated lines
4. **LSP diagnostics clean:** If applicable

### What NOT to Do
- ❌ Overvalidate - types should prevent invalid states
- ❌ Overcomment - code should be self-documenting
- ❌ Defensive coding - don't check for "impossible" states
- ❌ Premature optimization - make it work, then fast (if needed)
- ❌ Scope creep - only implement what's in the issue
- ❌ Suppress type errors with `as any` or `# type: ignore`

## Testing

### Current State
No automated test suite yet. Manual verification required:
- Deploy to local k3d cluster
- Test API endpoints manually
- Verify expected behavior

### Manual Testing Flow

```bash
# 1. Start cluster
k3d cluster create mcp-local

# 2. Deploy services
cd infra/k8s
helmfile sync

# 3. Wait for ready
kubectl wait --for=condition=Ready pod -l app=postgres-cluster -n database --timeout=300s

# 4. Port-forward
kubectl port-forward -n default svc/mycontextprotocol-gateway 8000:8000 &

# 5. Test ingest
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"content": "Test memory", "source": "api"}'

# 6. Check worker logs
kubectl logs -n default -l app=omni-worker -f

# 7. Verify database
kubectl exec -n database postgres-cluster-1 -it -- \
  psql -U postgres -c "SELECT * FROM inbox ORDER BY created_at DESC LIMIT 5;"
```

### When Tests Exist (Future)
- Run tests before claiming issue complete
- Add tests for new functionality
- Fix broken tests (don't skip/delete them)

## Documentation

### When to Update Docs
- Public API changes → Update API section in ARCHITECTURE.md
- New dependency → Update this file
- Architecture changes → Update ARCHITECTURE.md
- New patterns → Update CODE_STYLE.md

### Tone
- **Concise** - no fluff
- **Explicit** - be specific about versions, commands, paths
- **Practical** - focus on "how", minimal "why"

## Git Workflow

### Git Index Control

**CRITICAL:** The git staging area (index) is controlled by the user, not agents.

- **NEVER** run `git add` or `git commit` unless explicitly instructed by user
- User will review changes and stage them manually
- Implement changes, let user handle git operations
- Focus on making correct code changes, not managing git state

### Commits (when user instructs)
- **One logical change per commit**
- **Imperative mood:** "Add function" not "Added function"
- **Reference issues:** "Close #123: Add memory query endpoint"

### Before Pushing
```bash
git status        # Check what's staged
git diff --cached # Review changes
git commit -m "Clear description"
```

### Session End (CRITICAL)
See AGENTS.md "Landing the Plane" - must push to remote before ending session.

## Debugging

### Local K3s Issues
```bash
k3d cluster list               # Check cluster exists
kubectl get pods -A            # Check pod status
kubectl logs -n <ns> <pod>     # View logs
kubectl describe pod <pod>     # Detailed status
```

### Worker Issues
```bash
# Check ScaledJob status
kubectl get scaledjobs -n default

# Check if KEDA is triggering
kubectl get jobs -n default

# View worker logs
kubectl logs -n default -l app=omni-worker --tail=100

# Check queue depth
kubectl exec -n default dragonfly-0 -- redis-cli LLEN ingest-queue
```

### Database Issues
```bash
# Port-forward Postgres
kubectl port-forward -n database svc/postgres-cluster-rw 5432:5432

# Connect via psql
psql -h localhost -U postgres -d postgres

# Check tables
\dt

# Check recent inbox entries
SELECT id, content, processed, created_at FROM inbox 
ORDER BY created_at DESC LIMIT 10;
```

### Helm/Helmfile Issues
```bash
helmfile status                # Check release status
helm list -A                   # All releases
helm history <release> -n <ns> # Release history
```

## Getting Help

### Resources
1. **.agentinstructions/ARCHITECTURE.md** - System design, two-part split, State vs Tools
2. **CODE_STYLE.md** - Style conventions
3. **Issue description** - Specific requirements

### When Stuck
1. Search codebase for similar patterns
2. Check referenced documentation
3. Try the obvious solution (might just work)
4. If still stuck: **report blocker to user** (see "When Blocked" above)

## Anti-Patterns

### Don't
- ❌ Implement features not in the issue
- ❌ Refactor working code "to make it better"
- ❌ Add validation everywhere "just in case"
- ❌ Comment obvious code
- ❌ Copy-paste without understanding
- ❌ Commit without testing
- ❌ Leave debug prints/commented code
- ❌ Change formatting of unrelated files

### Do
- ✅ Ask when requirements are ambiguous
- ✅ Report problems early
- ✅ Write minimal code that solves the problem
- ✅ Use types to prevent errors
- ✅ Test your changes
- ✅ Update docs when APIs change
- ✅ Close issues when done

## Phase-Specific Context

### Phase 1: Infrastructure ✅ COMPLETE (2026-01-07)

**Completed**:
- ✅ Removed OpenFaaS from helmfile
- ✅ Added CloudNativePG operator
- ✅ Added Dragonfly (Redis-compatible queue + cache)
- ✅ Added KEDA (event-driven autoscaling)
- ✅ Deployed PostgreSQL cluster with pgvector
- ✅ Created database schema (6 tables: inbox + mem0 + llamaindex)

### Current Phase: Phase 1.5 (Development Toolchain)

**Goal**: Modernize dev environment before building application services.

**Active Work**:
- [ ] Update flake.nix (remove faas-cli, add uv/ruff/basedpyright/lefthook/go-task/k9s/stern)
- [ ] Create pyproject.toml (Python 3.13, dependencies, tool configs)
- [ ] Create Taskfile.yml (dev/lint/format/typecheck/db:* tasks)
- [ ] Create lefthook.yml (pre-commit: ruff/basedpyright, pre-push: task check)
- [ ] Setup Alembic (SQLAlchemy models → autogenerate migrations)
- [ ] Update documentation (✅ ARCHITECTURE.md, ⏳ DEVELOPMENT.md, ⏳ README.md)

**Key Decisions**:
- **Python 3.13** (NOT 3.12)
- **Alembic** (NOT Atlas - licensing issue)
- **SQLAlchemy models** as schema source (NOT init-schema.sql)
- **uv + uv2nix** for Python/Nix bridge

**What's NOT in scope yet**:
- Application services (gateway, worker) - Phase 2
- Query implementation - Phase 3
- OpenWebUI integration - Phase 4
- Caching, MinIO, advanced features - Phase 5 (Phase 2/3)

### Phase 2/3 Features (Deferred)

These are documented but NOT to be implemented in current phase:

- **Dragonfly context cache** - Cache Mem0 results with 5-30 min TTL
- **Query routing strategies** - Router LLM, fan-out, or hierarchical
- **MinIO file storage** - S3-compatible storage for PDFs/documents
- **Backup strategy** - Postgres → MinIO daily backups
- **Monitoring** - Prometheus, Grafana dashboards

**If asked to implement these**: Politely note they're Phase 2/3 and confirm with user before proceeding.

## Questions?

If this doc doesn't answer your question:
1. Check if it's a user decision (ask user)
2. Check if it's covered in CODE_STYLE.md
3. Check if it's architectural (ARCHITECTURE.md)
4. If still unclear: **ask the user**
