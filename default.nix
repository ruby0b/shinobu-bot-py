{ pkgs, ... }:
pkgs.python3Packages.buildPythonApplication {
  src = ./.;
  pname = "shinobu-bot-py";
  version = "1.0.0";
  propagatedBuildInputs = with pkgs.python3Packages; [
    setuptools
    aiohttp
    nextcord
    fuzzywuzzy
    feedparser
    aiocache
  ];
}
