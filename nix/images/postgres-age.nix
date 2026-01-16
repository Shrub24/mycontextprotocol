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
  name = "ghcr.io/shrub24/mycontextprotocol";
  tag = "postgres-age-latest";

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
