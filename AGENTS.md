# Agent Instructions

This project uses **bd** (beads) for issue tracking. Run `bd onboard` to get started.

## Architecture & Development Workflow

For complete project context, see:
- **[.agentinstructions/ARCHITECTURE.md](.agentinstructions/ARCHITECTURE.md)** - Full system architecture
- **[.agentinstructions/DEVELOPMENT.md](.agentinstructions/DEVELOPMENT.md)** - Agent development workflow
- **[CODE_STYLE.md](CODE_STYLE.md)** - Code conventions and standards

## Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --status in_progress  # Claim work
bd close <id>         # Complete work
bd sync               # Sync with git
```

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds

## Agent Selection for Research & Decision Making

When making **high-level architectural decisions** or researching technologies:

### Use `librarian` agent for:
- ✅ Technology evaluation and comparison
- ✅ Best practices and design patterns
- ✅ Industry trends and adoption (GitHub stars, blog posts, case studies)
- ✅ Library/framework maturity assessment
- ✅ Official documentation and guides
- ✅ Web search for modern patterns and solutions
- ✅ GitHub repository overview (README, issues, discussions)

### Use `explore` agent for:
- ✅ Finding code patterns **within our codebase**
- ✅ Understanding existing implementation details
- ✅ Locating where specific functionality lives in our code
- ✅ Cross-referencing our modules and patterns

### DON'T use `explore` for:
- ❌ Researching external libraries/frameworks
- ❌ Reading through third-party repository code
- ❌ Evaluating technology choices
- ❌ Finding best practices or design patterns

**Rule of thumb**: If you're asking "should we use X?" or "how does Y compare to Z?", use `librarian`. If you're asking "where in our code do we handle X?", use `explore`.

## Project Philosophy & Decision-Making

**THIS IS A FOSS PROJECT, NOT AN ENTERPRISE SYSTEM.**

### Core Values

1. **Cutting Edge Over Stability** - We prefer modern, forward-thinking technologies even if they're Beta/RC. The goal is to work with the most modern stack possible.

2. **Idiomatic & Clean** - Industry standard patterns (or future standard). Clean architecture. Powerful abstractions. No legacy cruft.

3. **Accessible but Experimental** - We want people to use this, but we're not optimizing for Fortune 500 deployment. Reasonable stability, but we can take risks.

4. **Personal Project First** - This is built for learning, exploration, and pushing boundaries. Commercial robustness is secondary.

### Technology Selection Criteria

When evaluating technologies, **prioritize in this order**:

1. **Modern & Forward-Thinking** - Is this where the industry is heading?
2. **Clean API & Idiomatic** - Does it feel right? Is it well-designed?
3. **Community Momentum** - Active development, good docs, real adoption?
4. **Operational Simplicity** - Can we run it without enterprise ops team?
5. **Stability** - Nice to have, but NOT a blocker if other criteria met

**Examples of this philosophy in action:**
- ✅ LightRAG (Beta, 27k stars, cutting edge graph RAG) over Neo4j (mature but heavy)
- ✅ Apache AGE (PostgreSQL extension) over separate graph database
- ✅ Python 3.13 (latest) over 3.11 (more stable)
- ✅ Dragonfly over Redis (modern, better ARM64 performance)
- ✅ KEDA + Containers over OpenFaaS (no framework lock-in)

**This is explicitly NOT an enterprise/production-critical system.** We're building something people can use and learn from, with modern patterns and cutting-edge tech.

