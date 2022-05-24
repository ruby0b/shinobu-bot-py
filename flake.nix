{
  description = "Shinobu - a Discord bot written in Python";

  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.flake-utils.inputs.nixpkgs.follows = "nixpkgs";
  inputs.mach-nix.url = "github:DavHau/mach-nix";
  inputs.mach-nix.inputs.nixpkgs.follows = "nixpkgs";
  inputs.mach-nix.inputs.flake-utils.follows = "flake-utils";

  outputs = { self, nixpkgs, flake-utils, mach-nix }:
    (flake-utils.lib.eachDefaultSystem (system:
      let
        python = "python39";
        pkgs = import nixpkgs { inherit system; };
        # https://github.com/DavHau/mach-nix/issues/153#issuecomment-717690154
        mach = import mach-nix { inherit pkgs python; };
        shinobu-bot = mach.buildPythonApplication {
          src = ./.;
          pname = "shinobu-bot";
          version = "1.0.0";
          requirements = ''
            aiohttp[speedups]
            discord.py[voice]
            fuzzywuzzy[speedup]
            feedparser
            aiocache
            async-property
          '';
        };
      in
      {
        packages = { inherit shinobu-bot; };
        defaultPackage = shinobu-bot;
        defaultApp = flake-utils.lib.mkApp { drv = shinobu-bot; exePath = "/bin/shinobu-bot.py"; };
        devShell = mach.mkPythonShell { packagesExtra = [ shinobu-bot ]; };
      }))
    // {
      nixosModules.default = { lib, config, ... }:
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
                ExecStart = self.defaultApp.x86_64-linux.program;
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
