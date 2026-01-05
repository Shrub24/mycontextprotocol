{
  description = "mycontextprotocol development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
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
          buildInputs = with pkgs; [
            # Core tools
            git
            beads
            
            # Infrastructure
            opentofu
            kubectl
            kubernetes-helm
            helmfile
            k3d
            
            # OpenFaaS
            faas-cli
            
            # Container runtime
            docker
            docker-compose
            
            # Utilities
            jq
            yq-go
            curl
            openssl
            
            # Optional: uncomment when needed
            # cloudflared
            # k9s
            # stern
            # postgresql
            # minio-client
          ];
          
          shellHook = ''
            echo "🚀 mycontextprotocol dev environment"
            echo ""
            echo "Available tools:"
            echo "  bd:        $(bd --version 2>/dev/null || echo 'bd (beads issue tracker)')"
            echo "  kubectl:   $(kubectl version --client -o json 2>/dev/null | jq -r '.clientVersion.gitVersion')"
            echo "  helm:      $(helm version --short 2>/dev/null | cut -d' ' -f1)"
            echo "  k3d:       $(k3d version 2>/dev/null | head -1)"
            echo "  tofu:      $(tofu version -json 2>/dev/null | jq -r '.terraform_version')"
            echo "  faas-cli:  $(faas-cli version 2>/dev/null | grep 'CLI' | awk '{print $2}')"
            echo ""
            echo "Quick start:"
            echo "  bd ready              # Check available issues"
            echo "  k3d cluster create    # Start local K3s cluster"
            echo "  helmfile sync         # Deploy services"
            echo ""
          '';
        };
      }
    );
}
