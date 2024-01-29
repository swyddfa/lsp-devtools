{
  description = "Developer tooling for language servers";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, utils }:
    {
      overlays.default = self: super:
        nixpkgs.lib.composeManyExtensions [
          (import ./lib/pytest-lsp/nix/pytest-lsp-overlay.nix)
          (import ./lib/lsp-devtools/nix/lsp-devtools-overlay.nix)
      ] self super;
    };
}
