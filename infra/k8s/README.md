# K3s Helmfile Deployment

This directory contains Helmfile configuration for deploying:
- **PostgreSQL** - Database
- **OpenFaaS** - Serverless functions platform
- **Cloudflared** - Cloudflare Tunnel for secure ingress
- **mem0** - Memory layer for AI applications

## Prerequisites

1. **k3s cluster** running
2. **kubectl** configured
3. **helm** installed
4. **helmfile** installed

```bash
# Install helmfile
curl -fsSL https://github.com/helmfile/helmfile/releases/download/v0.161.0/helmfile_0.161.0_linux_amd64.tar.gz | tar -xz
sudo mv helmfile /usr/local/bin/
```

## Setup

### 1. Cloudflare Tunnel Setup

First, create a Cloudflare tunnel:

```bash
# Install cloudflared
curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
sudo mv cloudflared /usr/local/bin/
sudo chmod +x /usr/local/bin/cloudflared

# Login and create tunnel
cloudflared tunnel login
cloudflared tunnel create k3s-cluster

# Get tunnel credentials
cloudflared tunnel info k3s-cluster
```

### 2. Set Environment Variables

```bash
export CLOUDFLARE_ACCOUNT_ID="your-account-id"
export CLOUDFLARE_TUNNEL_SECRET="your-tunnel-secret"
```

Or create a `.env` file:

```bash
cat > .env <<EOF
CLOUDFLARE_ACCOUNT_ID=your-account-id
CLOUDFLARE_TUNNEL_SECRET=your-tunnel-secret
EOF
```

### 3. Deploy

```bash
cd infra/k8s

# Sync all releases (default environment)
helmfile sync

# Or deploy to production
helmfile -e production sync

# Deploy specific release
helmfile -l name=postgresql sync
```

## Usage

### Access Services

**OpenFaaS Gateway:**
```bash
# Get admin password
kubectl get secret -n openfaas basic-auth -o jsonpath="{.data.basic-auth-password}" | base64 --decode

# Port forward
kubectl port-forward -n openfaas svc/gateway 8080:8080

# Login
echo -n <password> | faas-cli login --password-stdin
```

**PostgreSQL:**
```bash
# Connect to PostgreSQL
kubectl run postgresql-client --rm --tty -i --restart='Never' \
  --namespace database \
  --image docker.io/bitnami/postgresql:15 \
  --env="PGPASSWORD=changeme123" \
  --command -- psql --host postgresql -U myapp -d myapp -p 5432
```

**mem0:**
```bash
# Port forward
kubectl port-forward -n mem0 svc/mem0 8080:8080
```

### Cloudflare Tunnel Routes

Update `values/cloudflared-values.yaml` with your domains:
- `openfaas.yourdomain.com` → OpenFaaS Gateway
- `mem0.yourdomain.com` → mem0 API

Then configure DNS:
```bash
cloudflared tunnel route dns k3s-cluster openfaas.yourdomain.com
cloudflared tunnel route dns k3s-cluster mem0.yourdomain.com
```

## Management

### Update releases
```bash
helmfile diff    # See what will change
helmfile apply   # Apply changes
```

### Destroy
```bash
helmfile destroy
```

### Check status
```bash
helmfile status
kubectl get pods --all-namespaces
```

## Secrets Management

For production, use proper secrets management:

```bash
# Create secrets for mem0
kubectl create secret generic mem0-secrets \
  --namespace mem0 \
  --from-literal=api-key=your-api-key

# Update PostgreSQL password
kubectl create secret generic postgresql-secret \
  --namespace database \
  --from-literal=password=your-secure-password
```

## Troubleshooting

```bash
# Check helm releases
helm list --all-namespaces

# Check logs
kubectl logs -n openfaas deploy/gateway
kubectl logs -n mem0 deploy/mem0
kubectl logs -n cloudflare deploy/cloudflared

# Delete stuck releases
helmfile delete
helm delete <release-name> -n <namespace>
```

## Notes

- **Storage**: Uses k3s default `local-path` storage class
- **Networking**: Services use ClusterIP, exposed via Cloudflare Tunnel
- **Scaling**: Adjust replicas in environment files
- **Security**: Change default passwords before production use
