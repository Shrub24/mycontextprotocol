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

## Workflow

### 1. Check Work Queue
```bash
bd ready
```

Shows available issues prioritized P0 (critical) → P4 (low).

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
background_task(agent="explore", prompt="Locate error handling patterns used in functions/")
background_task(agent="librarian", prompt="Find best practices for OpenFaaS Python handlers")

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

### Examples

#### Good: Researching New Feature
```
User: "Add rate limiting to the API"

Agent thinking: I need to understand:
1. How the codebase currently handles middleware
2. Best practices for rate limiting in OpenFaaS
3. If there are existing examples

Actions:
- background_task(agent="explore", prompt="Find middleware patterns and request interceptors")
- background_task(agent="librarian", prompt="Research rate limiting strategies for OpenFaaS Python functions")
- Read obvious files like functions/stack.yml while agents run
```

#### Bad: Over-using Agents
```
User: "Add a comment to line 5 of handler.py"

Agent: Let me spawn an explore agent to find handler.py...
❌ WRONG - just read the file directly
```

### Collecting Results

```bash
# System notifies you when background tasks complete
# Retrieve results when needed:
background_output(task_id="task_abc123")

# Before final answer, always cancel remaining tasks:
background_cancel(all=true)
```

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

### 6. Complete
```bash
bd close <issue-id> --comment "Brief description of what was done"
```

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
BLOCKED: Cannot deploy Mem0 - image doesn't support ARM64

Context:
- Attempted to deploy mem0ai/mem0-api-server:latest
- Error: "no matching manifest for linux/arm64"

Options:
1. Use x86_64 image with QEMU emulation (slow, works)
2. Build ARM image from source (requires maintaining build)
3. Switch to Mem0 Python SDK + custom FastAPI wrapper (more work, full control)

Recommendation: Option 3 - gives us control and avoids emulation overhead.
Estimate: +2 days development time.

Should I proceed with Option 3?
```

## Code Quality

### Before Committing
1. **Types pass:** `basedpyright` clean on changed files
2. **Style passes:** `ruff check` clean
3. **No secrets:** Check for API keys, passwords in code
4. **Respects .editorconfig:** Don't reformat unrelated lines

### What NOT to Do
- ❌ Overvalidate - types should prevent invalid states
- ❌ Overcomment - code should be self-documenting
- ❌ Defensive coding - don't check for "impossible" states
- ❌ Premature optimization - make it work, then fast (if needed)
- ❌ Scope creep - only implement what's in the issue

## Testing

### Current State
No automated test suite yet. Manual verification required:
- Deploy to local k3d cluster
- Test API endpoints manually
- Verify expected behavior

### When Tests Exist
- Run tests before claiming issue complete
- Add tests for new functionality
- Fix broken tests (don't skip/delete them)

## Documentation

### When to Update Docs
- Public API changes → Update docstrings
- New tool/dependency → Update docs/development.md
- Architecture changes → Update .agentinstructions/ARCHITECTURE.md
- New patterns → Update CODE_STYLE.md

### Tone
- **Concise** - no fluff
- **Explicit** - be specific about versions, commands, paths
- **Practical** - focus on "how", minimal "why"

## Common Patterns

### Adding a New Function
1. Add to `functions/stack.yml`
2. Create `functions/<name>/handler.py`
3. Define I/O types with Pydantic models
4. Implement handler
5. Deploy: `faas-cli up`
6. Test manually

### Modifying Helm Values
1. Update `infra/k8s/values/common.yaml` (shared config)
2. OR update `values/local.yaml` or `values/production.yaml` (env-specific)
3. Apply: `helmfile sync`
4. Verify: `kubectl get all -n <namespace>`

### Adding Nix Dependencies
1. Edit `flake.nix` → add to `buildInputs`
2. Update lock: `nix flake update`
3. Verify: `nix develop` → check tool available
4. Update docs/development.md if it's a new workflow tool

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

### Function Issues
```bash
faas-cli list                  # Check deployed functions
faas-cli logs <function>       # View function logs
faas-cli describe <function>   # Function details
```

### Helm/Helmfile Issues
```bash
helmfile status                # Check release status
helm list -A                   # All releases
helm history <release> -n <ns> # Release history
```

## Getting Help

### Resources
1. **.agentinstructions/ARCHITECTURE.md** - System design
2. **CODE_STYLE.md** - Style conventions
3. **docs/development.md** - Environment setup
4. **Issue description** - Specific requirements

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

## Example Session

```bash
# 1. Check work
bd ready

# 2. Claim issue
bd update mycontextprotocol-xyz --status in_progress

# 3. Read requirements
bd show mycontextprotocol-xyz
cat .agentinstructions/ARCHITECTURE.md  # if needed

# 4. Implement
vim functions/add-memory/handler.py
basedpyright functions/add-memory/handler.py
ruff check functions/add-memory/handler.py

# 5. Test
faas-cli up -f functions/stack.yml
curl -X POST http://localhost:8080/function/add-memory -d '{"content":"test"}'

# 6. Complete
bd close mycontextprotocol-xyz --comment "Implemented add-memory endpoint with validation"
git add functions/add-memory/
git commit -m "Add memory ingestion endpoint

Closes mycontextprotocol-xyz

- Pydantic validation at boundary
- Store to inbox table
- Return 202 Accepted with ID"
```

## Questions?

If this doc doesn't answer your question:
1. Check if it's a user decision (ask user)
2. Check if it's covered in CODE_STYLE.md
3. Check if it's architectural (ARCHITECTURE.md)
4. If still unclear: **ask the user**
