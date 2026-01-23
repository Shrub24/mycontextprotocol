{ pkgs, nix2containerLib }:

let
  postgresql = pkgs.postgresql_17.withPackages (p: [
    p.age
    p.pgvector
  ]);

  root = pkgs.buildEnv {
    name = "postgres-age-root";
    paths = [ postgresql pkgs.bash pkgs.coreutils ];
    pathsToLink = [ "/bin" ];
  };
in
nix2containerLib.buildImage {
  name = "ghcr.io/shrub24/mycontextprotocol-postgres-age";
  tag = "17.7-mcp-0.0.1";

  copyToRoot = root;
  maxLayers = 100;

  config = {
    Cmd = [ "${postgresql}/bin/postgres" ];

    ExposedPorts = {
      "5432/tcp" = { };
    };

    Env = [
      "PATH=/bin"
      "PGDATA=/var/lib/postgresql/data"
    ];
  };
}
