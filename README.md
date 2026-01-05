# mycontextprotocol

> Self-hosted personal memory and context management system

**Status:** 🚧 Active Development

A cloud-agnostic, Kubernetes-based system for capturing, organizing, and querying personal context using hybrid AI (vector search + knowledge graphs).

## Overview

mycontextprotocol combines:
- **PostgreSQL + pgvector** for vector embeddings and structured storage
- **Mem0** for AI-powered fact extraction and knowledge graphs
- **MinIO** for object storage
- **OpenFaaS** for serverless functions
- **K3s** for lightweight orchestration

Designed for single-user deployment on Oracle Cloud Free Tier, but runs anywhere Kubernetes does.

## Quick Links

- [Architecture](.agentinstructions/ARCHITECTURE.md) - Full system design
- [Development Guide](docs/development.md) - Setup your dev environment
- [Code Style](CODE_STYLE.md) - Conventions and standards
- [Deployment Guide](docs/deployment.md) - Production deployment (coming soon)

## Quick Start

### Prerequisites

- Nix with flakes enabled
- Docker daemon running

### Get Started

```bash
# Clone and enter dev environment
git clone <repo>
cd mycontextprotocol
nix develop

# Check available work
bd ready

# Start local cluster (when implemented)
k3d cluster create --config k3d/local.yaml
```

## Project Structure

```
mycontextprotocol/
├── .agentinstructions/     # Architecture, agent workflows
├── functions/              # OpenFaaS Python functions
├── infra/
│   ├── k8s/               # Helmfile, Kubernetes manifests
│   └── tofu/              # OpenTofu infrastructure code
├── k3d/                   # K3d cluster configs
├── scripts/               # Helper scripts
└── docs/                  # Documentation
```

## Development

This project uses:
- **Nix flakes** for reproducible dev environments
- **bd (beads)** for issue tracking
- **Helmfile** for Kubernetes deployments
- **Python 3.13** for functions

See [docs/development.md](docs/development.md) for details.

## Architecture Highlights

- **Tri-layer data model:** Vault (cold storage), Library (hot vectors), Brain (AI memory)
- **Cloud-agnostic:** Runs on K3s anywhere (Oracle, Hetzner, local k3d)
- **FaaS-based:** All business logic in OpenFaaS Python functions
- **Zero-trust ingress:** Cloudflare Tunnel for production (no open ports)

See [.agentinstructions/ARCHITECTURE.md](.agentinstructions/ARCHITECTURE.md) for complete details.

## Contributing

This is a personal project, but contributions welcome. Follow:
1. Read [CODE_STYLE.md](CODE_STYLE.md)
2. Check `bd ready` for available work
3. Claim an issue: `bd update <id> --status in_progress`
4. Submit PR

## License

(To be determined)
