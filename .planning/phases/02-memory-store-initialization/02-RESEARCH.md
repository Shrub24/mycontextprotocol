# Phase 2: Memory store initialization - Research

**Researched:** 2026-01-16
**Domain:** Kubernetes service-to-service auth (Linkerd/mTLS + K8s identity) and Postgres multi-DB layout
**Confidence:** MEDIUM

<research_summary>
## Summary

Researched internal service authentication patterns (Linkerd, ServiceAccount JWT, SPIFFE) and Postgres layout tradeoffs for multi-store systems. Linkerd provides automatic mTLS with workload identity bound to Kubernetes ServiceAccounts, plus policy CRDs to authorize traffic. It does **not** remove the need for secrets (DB passwords, API keys), but it does provide a strong transport security baseline. ServiceAccount JWT validation via TokenReview is viable without a mesh but requires more application logic and careful audience/issuer checks.

For Postgres layout, separate databases provide the strongest isolation but block direct SQL joins across stores. Single database + schema-per-store is more join-friendly and centralizes extension management (pgvector/AGE), but reduces isolation. Given this project’s multi-store nature (Mem0/LlamaIndex/LightRAG), the idiomatic default is **multi-DB with application-level aggregation**, and only consolidate to single DB if you later require cross-store joins or a shared transactional model.

**Primary recommendation:** Keep multi-DB with shared credentials (SOPS-managed) now; defer Linkerd to Phase 6 unless you want to expand platform scope, because it adds control-plane complexity without removing secrets.
</research_summary>

<standard_stack>
## Standard Stack

The established tools for these domains:

### Core
| Library/Tool | Version | Purpose | Why Standard |
|-------------|---------|---------|--------------|
| Linkerd | 2.x | Service mesh with automatic mTLS + identity | Lightweight mesh, K8s-native identity bound to ServiceAccounts | 
| Kubernetes NetworkPolicy | v1 | Pod-to-pod network ACLs | Baseline in-cluster isolation layer | 
| Postgres | 17.x | Primary data store | Already used by CNPG; supports pgvector/AGE per DB |

### Supporting
| Library/Tool | Version | Purpose | When to Use |
|-------------|---------|---------|-------------|
| cert-manager | latest | Certificate lifecycle | If you want automated Linkerd trust anchor rotation |
| SPIFFE/SPIRE | latest | Workload identity | If you need workload IDs across clusters or beyond mesh |
| postgres_fdw | built-in | Cross-DB access | Only if multi-DB joins become mandatory |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Linkerd | ServiceAccount JWT + TokenReview | Simpler infra, but more app logic and no transport policy layer |
| Multi-DB | Single DB + schemas | Easier joins + extension mgmt; less isolation |
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Pattern 1: Linkerd mTLS + Policy CRDs
**What:** Inject Linkerd sidecars, enable automatic mTLS, and lock down traffic with `Server` + `AuthorizationPolicy` objects tied to ServiceAccounts.
**When to use:** You want zero-trust, identity-based allow rules for in-cluster traffic.
**Example:**
```bash
# Source: Linkerd install docs
linkerd install --crds | kubectl apply -f -
linkerd install | kubectl apply -f -
linkerd check
```
```bash
# Enable injection on a namespace
kubectl annotate ns <ns> linkerd.io/inject=enabled
```

### Pattern 2: ServiceAccount JWT + TokenReview
**What:** Services validate incoming JWTs by calling the Kubernetes TokenReview API with audience/issuer checks.
**When to use:** You need auth without a mesh and can accept app-level validation logic.
**Example:**
```yaml
# TokenReview API (Kubernetes auth)
apiVersion: authentication.k8s.io/v1
kind: TokenReview
spec:
  token: "<jwt>"
```

### Pattern 3: Multi-DB + app-level aggregation
**What:** Keep Mem0, LlamaIndex, LightRAG in separate DBs; correlate via shared `ingestion_id` and merge results in application code.
**When to use:** You value isolation and avoid cross-DB joins.

### Anti-Patterns to Avoid
- **Relying on mTLS without NetworkPolicy:** encrypted traffic still allows lateral movement.
- **Building custom JWT verification logic:** use TokenReview or a mesh identity system.
- **Using FDW for frequent cross-store joins:** adds latency and coupling.
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| mTLS between services | Custom TLS wrapper | Linkerd or SPIFFE/SPIRE | Identity + rotation is complex and error-prone |
| JWT validation for pod auth | Custom token parsing | TokenReview API | Avoid subtle auth bugs and audience misuse |
| Cross-DB joins | DIY query stitching | App-level aggregation or FDW | Joins across DBs are slow and fragile |

**Key insight:** Platform-level identity (Linkerd/SPIRE) and Postgres-native isolation patterns are hard to reimplement correctly.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: ServiceAccount JWT accepted without `aud` validation
**What goes wrong:** Tokens intended for the API server are accepted by services.
**Why it happens:** Audience checks are skipped.
**How to avoid:** Enforce `aud` and issuer checks or use TokenReview.
**Warning signs:** Tokens validate locally but fail when rotated or scoped.

### Pitfall 2: Linkerd cert rotation surprises
**What goes wrong:** mesh traffic breaks when trust anchors expire.
**Why it happens:** rotation isn’t planned.
**How to avoid:** follow Linkerd rotation guide or integrate cert-manager.
**Warning signs:** sudden TLS failures after 1 year.

### Pitfall 3: Relying on mTLS without NetworkPolicy
**What goes wrong:** a compromised pod can still reach internal services.
**Why it happens:** traffic is encrypted but not restricted.
**How to avoid:** add NetworkPolicy to reduce blast radius.
**Warning signs:** lateral movement possible within namespace.
</common_pitfalls>

<code_examples>
## Code Examples

### Linkerd install and validation
```bash
# Source: https://linkerd.io/2-edge/tasks/install/
linkerd install --crds | kubectl apply -f -
linkerd install | kubectl apply -f -
linkerd check
```

### TokenReview for JWT validation
```yaml
# Source: https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.35/#tokenreview-v1-authentication-k8s-io
apiVersion: authentication.k8s.io/v1
kind: TokenReview
spec:
  token: "<jwt>"
```
</code_examples>

<sota_updates>
## State of the Art (2024-2025)

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| App-level auth only | Service mesh mTLS + policy | 2020+ | Identity + encrypted transport by default |
| DB-per-service only | Schema-per-service where joins needed | ongoing | Centralized extension management |

**New tools/patterns to consider:**
- Linkerd policy CRDs (`Server`, `AuthorizationPolicy`) for identity-bound access.
- cert-manager integration for mesh identity rotation.

**Deprecated/outdated:**
- Long-lived, non-rotated mesh trust anchors.
</sota_updates>

<open_questions>
## Open Questions

1. **Do we want to introduce Linkerd in Phase 2 or defer to Phase 6?**
   - What we know: Linkerd is lightweight and idiomatic but adds control-plane + rotation work.
   - Recommendation: Defer unless platform work is desired now.

2. **Will cross-store SQL joins be needed?**
   - What we know: Multi-DB avoids collisions; joins are blocked without FDW.
   - Recommendation: Keep multi-DB and aggregate in app, revisit if joins become required.
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- https://linkerd.io/2-edge/reference/architecture/
- https://linkerd.io/2-edge/tasks/install/
- https://linkerd.io/2-edge/features/automatic-mtls/
- https://linkerd.io/2-edge/features/server-policy/
- https://kubernetes.io/docs/reference/access-authn-authz/authentication/#service-account-tokens
- https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.35/#tokenreview-v1-authentication-k8s-io
- https://kubernetes.io/docs/concepts/services-networking/network-policies/
- https://postgresql.org/docs/current/manage-ag-overview.html
- https://postgresql.org/docs/current/sql-createextension.html
- https://postgresql.org/docs/current/postgres-fdw.html

### Secondary (MEDIUM confidence)
- https://www.crunchydata.com/blog/designing-your-postgres-database-for-multi-tenancy
- https://fluxcd.io/flux/guides/repository-structure/
- https://cloud.google.com/blog/products/devops-sre/the-gitops-repository-structure-monorepo-vs-polyrepo-and-best-practices-17399ae6f3f4
- https://www.hashicorp.com/blog/terraform-mono-repo-vs-multi-repo-the-great-debate

### Tertiary (LOW confidence)
- None
</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: Linkerd mTLS + Kubernetes auth + Postgres layout
- Ecosystem: cert-manager, SPIFFE/SPIRE, postgres_fdw
- Patterns: service mesh policy, TokenReview validation, multi-DB aggregation
- Pitfalls: JWT audience misuse, mesh rotation, missing NetworkPolicy

**Confidence breakdown:**
- Standard stack: MEDIUM (mesh + auth + DB layout span multiple domains)
- Architecture: MEDIUM (vendor-specific policy details may vary)
- Pitfalls: HIGH (documented in official docs)
- Code examples: HIGH (official docs)

**Research date:** 2026-01-16
**Valid until:** 2026-02-16
</metadata>

---

*Phase: 02-memory-store-initialization*
*Research completed: 2026-01-16*
*Ready for planning: yes*
