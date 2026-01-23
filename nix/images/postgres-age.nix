{ pkgs, nix2containerLib }:

let
  postgresql = pkgs.postgresql_17.withPackages (p: [
    p.age
    p.pgvector
  ]);

  passwd = pkgs.writeText "postgres-passwd" ''
root:x:0:0:root:/root:/bin/sh
postgres:x:26:26:PostgreSQL:/var/lib/postgresql:/bin/sh
'';

  group = pkgs.writeText "postgres-group" ''
root:x:0:
postgres:x:26:
'';

  etcDir = pkgs.runCommand "postgres-etc" {} ''
    mkdir -p $out/etc
    cp ${passwd} $out/etc/passwd
    cp ${group} $out/etc/group
  '';

  runtimeDirs = pkgs.runCommand "postgres-runtime-dirs" {} ''
    mkdir -p $out/var/lib/postgresql
  '';

  root = pkgs.buildEnv {
    name = "postgres-age-root";
    paths = [ postgresql pkgs.bash pkgs.coreutils etcDir runtimeDirs ];
    pathsToLink = [ "/bin" "/etc" "/var" "/share" "/lib" ];
  };
in
nix2containerLib.buildImage {
  name = "ghcr.io/shrub24/mycontextprotocol-postgres-age";
  tag = "17.7-mcp-0.0.1";

  copyToRoot = root;
  maxLayers = 100;

  config = {
    Cmd = [ "${postgresql}/bin/postgres" ];
    User = "26:26";

    ExposedPorts = {
      "5432/tcp" = { };
    };

    Env = [
      "PATH=/bin"
      "PGDATA=/var/lib/postgresql/data"
    ];
  };

  perms = [
    {
      path = "/var/lib/postgresql";
      regex = ".*";
      mode = "0777";
    }
  ];
}
