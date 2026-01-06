{
  description = "mycontextprotocol development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    uv2nix.url = "github:pyproject-nix/uv2nix";
    uv2nix.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = { self, nixpkgs, flake-utils, uv2nix }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        
        beads = pkgs.stdenv.mkDerivation rec {
          pname = "beads";
          version = "0.44.0";
          
          src = pkgs.fetchurl {
            url = "https://github.com/steveyegge/beads/releases/download/v${version}/beads_${version}_linux_amd64.tar.gz";
            sha256 = "c3881191cb20dfc7089d7966856e9c19cb09c1c92e7c8496eec71dfd0f5ef551";
          };
          
          sourceRoot = ".";
          
          installPhase = ''
            mkdir -p $out/bin
            cp bd $out/bin/bd
            chmod +x $out/bin/bd
          '';
        };
      in
      {
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            # Core tools
            git
            beads
            
            # Python tooling
            python313
            uv
            ruff
            basedpyright
            
            # Pre-commit & tasks
            lefthook
            go-task
            
            # Infrastructure
            opentofu
            kubectl
            kubernetes-helm
            helmfile
            k3d
            
            # K8s debugging
            k9s
            stern
            
            # Container runtime
            docker
            docker-compose
            
            # Utilities
            jq
            yq-go
            curl
            openssl
            
            # C/C++ libraries for Python native extensions
            stdenv.cc.cc.lib
            
            # Optional (for production)
            # cloudflared
            # postgresql
            # minio-client
          ];
          
          LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib";
          
          shellHook = ''
            cat <<'EOF'
🚀 mycontextprotocol dev environment

Quick start:
  uv sync               Install Python dependencies
  task --list           Show all available tasks
  task check            Run quality checks (format + lint + typecheck)
  bd ready              Check available issues
  
Cluster ops:
  task cluster:create   Create local k3d cluster
  task deploy           Deploy services with helmfile
  helmfile sync         Direct helmfile deployment (from infra/k8s/)
  
Database:
  task db:autogenerate -- "msg"   Generate migration from models
  task db:upgrade                 Apply migrations
  
Development:
  task dev              Run gateway with hot-reload
  task logs -- <pod>    Stream logs from pods
EOF
          '';
        };
      }
    );
}
