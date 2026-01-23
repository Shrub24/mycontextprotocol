{
  pkgs,
  # pyproject-nix,
  # uv2nix,
  # pyproject-build-systems,
  workspace,
  pythonSet,
  nix2containerLib,
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

  runtimeDirs = pkgs.runCommand "worker-runtime-dirs" {} ''
    mkdir -p $out/app $out/tmp
  '';

  root = pkgs.buildEnv {
    name = "worker-root";
    paths = [ venv runtimeDirs ];
    pathsToLink = [ "/venv" ];
  };
in
  nix2containerLib.buildImage {
    name = "ghcr.io/shrub24/mycontextprotocol-worker";
    tag = "0.0.1";

    copyToRoot = root;
    maxLayers = 100;

    config = {
      Cmd = ["/venv/bin/python" "-m" "mycontextprotocol.worker"];
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

    perms = [
      {
        path = "/tmp";
        regex = ".*";
        mode = "0777";
      }
    ];
  }
