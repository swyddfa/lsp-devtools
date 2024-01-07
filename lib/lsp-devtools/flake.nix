{
  description = "lsp-devtools: Developer tooling for language servers";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    utils.url = "github:numtide/flake-utils";
  };

   outputs = { self, nixpkgs, utils }:

     let
       eachPythonVersion = versions: f:
         builtins.listToAttrs (builtins.map (version: {name = "py${version}"; value = f version; }) versions);    in {

      overlays.default = import ./nix/lsp-devtools-overlay.nix;

      packages = utils.lib.eachDefaultSystemMap (system:
        let
          pkgs = import nixpkgs { inherit system; overlays = [ self.overlays.default ]; };
        in
          eachPythonVersion [ "38" "39" "310" "311"] (pyVersion:
            pkgs."python${pyVersion}Packages".lsp-devtools
          )
      );
    };
}
