{
  description = "Developer tooling for language servers";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, utils }:
    {
      overlays.default =  import ./lib/pytest-lsp/nix/pytest-lsp-overlay.nix;
    };
}
