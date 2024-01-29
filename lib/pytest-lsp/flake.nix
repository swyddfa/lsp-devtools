{
  description = "pytest-lsp: End to end testing of language servers with pytest";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    utils.url = "github:numtide/flake-utils";
  };

   outputs = { self, nixpkgs, utils }:

     let
       eachPythonVersion = versions: f:
         builtins.listToAttrs (builtins.map (version: {name = "py${version}"; value = f version; }) versions);
      pytest-lsp-overlay = import ./nix/pytest-lsp-overlay.nix;
    in {

      overlays.default = pytest-lsp-overlay;

      packages = utils.lib.eachDefaultSystemMap (system:
        let
          pkgs = import nixpkgs { inherit system; overlays = [ pytest-lsp-overlay ]; };
        in
          eachPythonVersion [ "38" "39" "310" "311"] (pyVersion:
            pkgs."python${pyVersion}Packages".pytest-lsp
          )
      );

      devShells = utils.lib.eachDefaultSystemMap (system:
        let
          pkgs = import nixpkgs { inherit system; overlays = [ pytest-lsp-overlay ]; };
        in
          eachPythonVersion [ "38" "39" "310" "311" ] (pyVersion:
            with pkgs; mkShell {
              name = "py${pyVersion}";

              shellHook = ''
                export PYTHONPATH="./:$PYTHONPATH"
              '';

              packages = with pkgs."python${pyVersion}Packages"; [
                pygls
                pytest
                pytest-asyncio
              ];
            }
          )
      );
    };
}
