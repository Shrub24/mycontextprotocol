{ pkgs }:

let
  postgresql = pkgs.postgresql_17.withPackages (p: [
    p.age
    p.pgvector
  ]);
in
pkgs.dockerTools.streamLayeredImage {
  name = "ghcr.io/shrub24/mycontextprotocol";
  tag = "postgres-age-latest";

  contents = [ postgresql pkgs.bash pkgs.coreutils ];

  config = {
    Cmd = [ "${postgresql}/bin/postgres" ];
    
    ExposedPorts = {
      "5432/tcp" = { };
    };
    
    Env = [
      "PATH=${postgresql}/bin:/bin"
      "PGDATA=/var/lib/postgresql/data"
    ];
  };
}
