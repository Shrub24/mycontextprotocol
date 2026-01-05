# Development Environment

This project uses **Nix flakes** for reproducible development environments. All tooling (kubectl, helm, k3d, OpenTofu, bd, etc.) is pinned to specific versions.

## Prerequisites

### 1. Install Nix

**Linux / WSL:**
```bash
sh <(curl -L https://nixos.org/nix/install) --daemon
```

### 2. Enable Flakes

Add to `~/.config/nix/nix.conf` (create if missing):
```
experimental-features = nix-command flakes
```

Restart the Nix daemon:
```bash
sudo systemctl restart nix-daemon
```

### 3. Docker Daemon (Required)

k3d requires a running Docker daemon. Install via your system package manager:

**Ubuntu/Debian:**
```bash
sudo apt-get install docker.io
sudo usermod -aG docker $USER
```

Log out and back in for group changes to take effect.

## Entering the Dev Environment

### Option A: Manual (nix develop)

```bash
nix develop
```

This drops you into a shell with all tools available. Verify:
```bash
bd --version
kubectl version --client
helm version
k3d version
tofu version
faas-cli version
```

### Option B: Automatic (direnv - Recommended)

Install direnv:
```bash
# Via your package manager
sudo apt-get install direnv  # Debian/Ubuntu
# OR via Nix
nix profile install nixpkgs#direnv
```

Hook into your shell (`~/.bashrc` or `~/.zshrc`):
```bash
eval "$(direnv hook bash)"  # or zsh
```

Allow the project:
```bash
cd /path/to/mycontextprotocol
direnv allow
```

Now the dev environment auto-activates when you `cd` into the repo.

## Available Tools

| Tool | Purpose |
|------|---------|
| `bd` | Beads issue tracker (pinned v0.44.0) |
| `kubectl` | Kubernetes CLI |
| `helm` | Kubernetes package manager |
| `helmfile` | Declarative Helm releases |
| `k3d` | k3s in Docker (local clusters) |
| `tofu` | OpenTofu (Terraform fork) |
| `faas-cli` | OpenFaaS CLI |
| `docker` | Docker CLI (daemon must be system-installed) |
| `jq`, `yq` | JSON/YAML processors |

## Quick Start

### 1. Check Project Status
```bash
bd ready
```

### 2. Start Local K3s Cluster
```bash
k3d cluster create mcp-local --servers 1 --agents 0
```

### 3. Deploy Services (when helmfile is ready)
```bash
cd infra/k8s
helmfile sync
```

### 4. Deploy Functions (when stack.yml is ready)
```bash
cd functions
faas-cli up
```

## Production Deployment

Production deployment uses the same tools but targets Oracle Cloud. See:
- `docs/deployment.md` for cloud provisioning
- `.agentinstructions/ARCHITECTURE.md` for full architecture

## Troubleshooting

### "command not found: nix"
Nix isn't installed. Follow [Prerequisites](#prerequisites).

### "experimental-features" error
Flakes aren't enabled. See [Enable Flakes](#2-enable-flakes).

### "Cannot connect to Docker daemon"
The Docker daemon isn't running:
```bash
sudo systemctl start docker
sudo systemctl enable docker
```

### direnv: error .envrc is blocked
Run `direnv allow` in the project directory.

## Adding New Tools

Edit `flake.nix` and add to `buildInputs`:
```nix
buildInputs = with pkgs; [
  # ... existing tools
  your-new-tool
];
```

Update the flake lock:
```bash
nix flake update
```

## Future: Production Ingress

When deploying production, you'll need:
- **Cloudflared** (Cloudflare Tunnel) - currently commented in `flake.nix`
- Cloudflare API token for tunnel creation

Uncomment `cloudflared` in `flake.nix` when ready.
