{
  pkgs,
  pyproject-nix,
  uv2nix,
  pyproject-build-systems,
  workspace,
  pythonSet,
  ...
}:
let
  baseVenv = (pythonSet.mkVirtualEnv "mycontextprotocol-worker-env" workspace.deps.default).overrideAttrs (old: {
    # Ignore collision between llama-parse and llama-cloud-services packages
    venvIgnoreCollisions = [ "*" ];
  });
  
  venv = pkgs.buildEnv {
    name = "mycontextprotocol-worker-env-wrapped";
    paths = [ baseVenv ];
    ignoreCollisions = true;  # llama-parse and llama-cloud-services both provide llama-parse binary
  };
in
  pkgs.dockerTools.streamLayeredImage {
    name = "ghcr.io/shrub24/mycontextprotocol";
    tag = "worker-latest";

    contents = [ venv ];

    config = {
      Cmd = ["${venv}/bin/python" "-m" "mycontextprotocol.worker"];
      Env = [
        "PYTHONUNBUFFERED=1"
        "PYTHONDONTWRITEBYTECODE=1"
      ];
      User = "65534:65534";
      WorkingDir = "/app";
      Labels = {
        "org.opencontainers.image.source" = "https://github.com/shrub24/mycontextprotocol";
        "org.opencontainers.image.description" = "Omni-Worker for mycontextprotocol memory ingestion";
        "org.opencontainers.image.licenses" = "MIT";
      };
      StopSignal = "SIGTERM";
    };

    fakeRootCommands = ''
      mkdir -p /app /tmp
      chmod 1777 /tmp
      chown -R 65534:65534 /app
    '';

    enableFakechroot = true;
    includeStorePaths = false;
    maxLayers = 100;
  }