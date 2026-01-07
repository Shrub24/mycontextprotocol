{ pkgs, lib, pyproject-nix, uv2nix, pyproject-build-systems }:

let
  workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ../..; };
  
  overlay = workspace.mkPyprojectOverlay {
    sourcePreference = "wheel";
  };
  
  python = pkgs.python313;
  
  pythonSet = (pkgs.callPackage pyproject-nix.build.packages {
    inherit python;
  }).overrideScope (
    lib.composeManyExtensions [
      pyproject-build-systems.overlays.default
      overlay
    ]
  );
  
  venv = pythonSet.mkVirtualEnv "mycontextprotocol-gateway" workspace.deps.default;
in
pkgs.dockerTools.streamLayeredImage {
  name = "ghcr.io/shrub24/mycontextprotocol";
  tag = "gateway-latest";

  contents = [ venv pkgs.bash pkgs.coreutils ];

  config = {
    Cmd = [ "${venv}/bin/python" "-m" "mycontextprotocol.gateway" ];
    
    ExposedPorts = {
      "8000/tcp" = { };
    };

    Env = [
      "PATH=${venv}/bin:/bin"
      "PYTHONUNBUFFERED=1"
    ];

    WorkingDir = "/app";
  };
}
