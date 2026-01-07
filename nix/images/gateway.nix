{ pkgs }:
let
  python = pkgs.python313;

  mycontextprotocol = python.pkgs.buildPythonPackage rec {
    pname = "mycontextprotocol";
    version = "0.1.0";
    format = "pyproject";

    src = ../../.;

    nativeBuildInputs = [ python.pkgs.hatchling ];

    propagatedBuildInputs = with python.pkgs; [
      fastapi
      uvicorn
      httpx
      sqlalchemy
      alembic
      psycopg
      pydantic-settings
      redis
      pgvector
    ];

    pythonImportsCheck = [ "mycontextprotocol" ];

    meta = {
      description = "Self-hosted personal memory and context management system";
      homepage = "https://github.com/code-yeongyu/mycontextprotocol";
    };
  };
in
pkgs.dockerTools.buildLayeredImage {
  name = "ghcr.io/code-yeongyu/mycontextprotocol";
  tag = "gateway-latest";

  contents = [
    python
    mycontextprotocol
    pkgs.coreutils
  ];

  config = {
    Cmd = [
      "${python}/bin/python"
      "-m"
      "uvicorn"
      "mycontextprotocol.gateway:app"
      "--host"
      "0.0.0.0"
      "--port"
      "8000"
    ];

    ExposedPorts = {
      "8000/tcp" = { };
    };

    Env = [
      "PYTHONUNBUFFERED=1"
      "PYTHONDONTWRITEBYTECODE=1"
    ];
  };
}
