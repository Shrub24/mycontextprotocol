{
  pkgs,
  pyproject-nix,
  uv2nix,
  pyproject-build-systems,
  workspace,
  pythonSet,
  nix2containerLib,
  ...
}:
let
  baseVenv = pythonSet.mkVirtualEnv "mycontextprotocol-gateway-env" workspace.deps.default;
  
  venv = (pythonSet.mkVirtualEnv "mycontextprotocol-gateway-env" workspace.deps.default).overrideAttrs (old: {
    # Ignore collision between llama-parse and llama-cloud-services packages
    venvIgnoreCollisions = [ "*" ];
  });

  root = pkgs.buildEnv {
    name = "gateway-root";
    paths = [ venv ];
    pathsToLink = [ "/venv" ];
  };
in
  nix2containerLib.buildImage {
    name = "ghcr.io/shrub24/mycontextprotocol";
    tag = "gateway-latest";

    copyToRoot = root;
    maxLayers = 100;

    config = {
      Cmd = ["/venv/bin/python" "-m" "mycontextprotocol.gateway"];
      ExposedPorts = {
        "8000/tcp" = {};
      };
      Env = [
        "PYTHONUNBUFFERED=1"
        "PYTHONDONTWRITEBYTECODE=1"
      ];
      User = "65534:65534";
      WorkingDir = "/app";
      Labels = {
        "org.opencontainers.image.source" = "https://github.com/shrub24/mycontextprotocol";
        "org.opencontainers.image.description" = "FastAPI Gateway for mycontextprotocol memory backend";
        "org.opencontainers.image.licenses" = "MIT";
      };
      Healthcheck = {
        Test = ["CMD" "/venv/bin/python" "-c" "import urllib.request; urllib.request.urlopen('http://localhost:8000/livez').read()"];
        Interval = 30000000000;
        Timeout = 5000000000;
        Retries = 3;
        StartPeriod = 10000000000;
      };
    };

    runAsRoot = ''
      mkdir -p /app /tmp
      chmod 1777 /tmp
      chown -R 65534:65534 /app
    '';
  }
