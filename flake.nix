{
  description = "Shinobu - a Discord bot written in Python";

  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.flake-utils.inputs.nixpkgs.follows = "nixpkgs";

  outputs = { self, nixpkgs, flake-utils }:
    (flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
      in
      rec {
        packages.shinobu-bot-py = import ./default.nix { inherit pkgs; };
        packages.default = packages.shinobu-bot-py;
        apps.default = flake-utils.lib.mkApp { drv = packages.shinobu-bot-py; exePath = "/bin/shinobu-bot.py"; };
      }))
    // {
      overlays.default = final: _: { shinobu-bot-py = import ./default.nix { pkgs = final; }; };
      nixosModules.default = { lib, config, pkgs, ... }:
        let
          inherit (lib) mkOption types mkIf;
          name = "shinobu-bot-py";
          cfg = config.services.${name};
        in
        {
          options.services.${name} = {
            enable = mkOption { type = types.bool; default = false; };
            stateDir = mkOption { type = types.str; default = name; };
            token = mkOption { type = types.uniq types.str; };
          };
          config = mkIf cfg.enable {
            systemd.services.${name} = {
              description = "Shinobu - a Discord bot written in Python";
              wantedBy = [ "multi-user.target" ];
              after = [ "network.target" ];

              serviceConfig = {
                ExecStart = "${pkgs.shinobu-bot-py}/bin/shinobu-bot.py";
                WorkingDirectory = "/var/lib/${cfg.stateDir}";
                StateDirectory = cfg.stateDir;
                Restart = "always";
                RestartSec = 20;
                DynamicUser = true;
              };

              preStart = ''
                mkdir -p data logs
                echo '${cfg.token}' >data/TOKEN
              '';
            };
          };
        };
    };
}
