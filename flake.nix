{
  description = "mycontextprotocol development environment";

  nixConfig = {
    extra-substituters = [
      "https://shrub24.cachix.org"
      "https://cache.nixos.org"
    ];
    extra-trusted-public-keys = [
      "shrub24.cachix.org-1:QMgWTCaMI7DSDdmvmKrsQ9cQwwTfw3zWRFz2yuxeriU="
      "cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY="
    ];
  };

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";

    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    nix2container = {
      url = "github:nlewo/nix2container";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, pyproject-nix, uv2nix, pyproject-build-systems, nix2container }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f system);
    in
    {
      packages = forAllSystems (system:
        let
          pkgs = import nixpkgs { inherit system; };
          nix2containerLib = nix2container.packages.${system}.nix2container;
          workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };
          
          # Create overlay from workspace dependencies
          workspaceOverlay = workspace.mkPyprojectOverlay {
            sourcePreference = "wheel";
          };
          
          # Get build-systems overlay
          buildSystemsOverlay = pyproject-build-systems.overlays.default;
          
          # Compose overlays (build-systems first, then workspace)
          overlay = pkgs.lib.composeManyExtensions [
            buildSystemsOverlay
            workspaceOverlay
          ];
          
          python = pkgs.python313;
          
          # Create pythonSet with composed overlay
          pythonSet = (pkgs.callPackage pyproject-nix.build.packages {
            inherit python;
          }).overrideScope overlay;
        in
        {
          gateway-image = pkgs.callPackage ./nix/images/gateway.nix {
            inherit pkgs pyproject-nix uv2nix pyproject-build-systems;
            inherit workspace pythonSet nix2containerLib;
          };
          worker-image = pkgs.callPackage ./nix/images/worker.nix {
            inherit pkgs pyproject-nix uv2nix pyproject-build-systems;
            inherit workspace pythonSet nix2containerLib;
          };
          postgres-age-image = pkgs.callPackage ./nix/images/postgres-age.nix {
            inherit pkgs nix2containerLib;
          };
        }
      );

      devShells = forAllSystems (system:
        let
          pkgs = import nixpkgs { inherit system; };
        in
        {
          default = pkgs.mkShell {
            buildInputs = with pkgs; [
              python313
              uv
              ruff
              basedpyright

              kubectl
              kubernetes-helm
              helmfile
              k3d
              k9s
              stern
              kubeconform
              kube-linter
              yamllint
              yamlfmt

              docker
              trivy
              go-task
              lefthook
              opentofu
              sops
              age
            ];

            shellHook = ''
              export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
              echo "mycontextprotocol dev environment loaded"
              echo "- Python: $(python --version)"
              echo "- UV: $(uv --version)"
              echo "- Kubectl: $(kubectl version --client --short 2>/dev/null || echo 'not connected')"
            '';
          };
        }
      );
    };
}
