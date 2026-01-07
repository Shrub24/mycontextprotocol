{
  description = "mycontextprotocol development environment";

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
  };

  outputs = { self, nixpkgs, pyproject-nix, uv2nix, pyproject-build-systems }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f system);
    in
    {
      packages = forAllSystems (system:
        let
          pkgs = import nixpkgs { inherit system; };
        in
        {
          gateway-image = pkgs.callPackage ./nix/images/gateway.nix {
            inherit pkgs pyproject-nix uv2nix pyproject-build-systems;
          };
          worker-image = pkgs.callPackage ./nix/images/worker.nix {
            inherit pkgs pyproject-nix uv2nix pyproject-build-systems;
          };
          postgres-age-image = pkgs.callPackage ./nix/images/postgres-age.nix {
            inherit pkgs;
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

              docker
              go-task
              lefthook
              opentofu
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
