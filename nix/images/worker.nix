{ pkgs }:
let
  python = pkgs.python313;

  appPackage = pkgs.stdenv.mkDerivation {
    name = "mycontextprotocol-app";

    src = ../../.;

    buildInputs = [ python ];

    installPhase = ''
      mkdir -p $out/lib/mycontextprotocol
      cp -r src/mycontextprotocol/* $out/lib/mycontextprotocol/

      mkdir -p $out/lib
      cp pyproject.toml $out/lib/
      cp uv.lock $out/lib/
    '';
  };
in
pkgs.dockerTools.buildLayeredImage {
  name = "ghcr.io/shrub24/mycontextprotocol";
  tag = "worker-latest";

  contents = [
    python
    python.pkgs.pip
    appPackage
    pkgs.coreutils
    pkgs.bash
  ];

  config = {
    Cmd = [
      "/bin/bash"
      "-c"
      "cd /app/lib && pip install --no-cache-dir -e . && cd /app && python -m mycontextprotocol.worker"
    ];

    WorkingDir = "/app";

    Env = [
      "PYTHONUNBUFFERED=1"
      "PYTHONDONTWRITEBYTECODE=1"
      "PATH=/app/lib:${python}/bin:/bin"
      "PYTHONPATH=/app/lib"
    ];
  };
}
