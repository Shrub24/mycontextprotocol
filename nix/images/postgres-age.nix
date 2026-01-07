{ pkgs }:
let
  postgres = pkgs.postgresql_16;
in
pkgs.dockerTools.buildLayeredImage {
  name = "ghcr.io/shrub24/mycontextprotocol";
  tag = "postgres-age-latest";

  contents = [
    postgres
    postgres.pkgs.age
  ];

  config = {
    Cmd = [
      "${postgres}/bin/postgres"
      "-D"
      "/var/lib/postgresql/data"
      "-c"
      "shared_preload_libraries=age"
      "-c"
      "max_connections=200"
      "-c"
      "shared_buffers=256MB"
      "-c"
      "work_mem=4MB"
      "-c"
      "maintenance_work_mem=64MB"
      "-c"
      "effective_cache_size=1GB"
      "-c"
      "checkpoint_completion_target=0.9"
      "-c"
      "wal_buffers=16MB"
    ];

    ExposedPorts = {
      "5432/tcp" = { };
    };

    Env = [
      "PGDATA=/var/lib/postgresql/data"
      "POSTGRES_USER=postgres"
      "POSTGRES_DB=postgres"
    ];

    Volumes = {
      "/var/lib/postgresql/data" = { };
    };
  };
}
