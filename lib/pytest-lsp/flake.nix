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

    devShells = utils.lib.eachDefaultSystemMap (system:
      let
        pkgs = import nixpkgs { inherit system; overlays = [ pytest-lsp-overlay ]; };
      in
        eachPythonVersion [ "37" "38" "39" "310" "311" ] (pyVersion:


          let
            pytest-lsp = pkgs."python${pyVersion}Packages".pytest-lsp.overridePythonAttrs (_: { doCheck = false; });
          in

          with pkgs; mkShell {
            name = "py${pyVersion}";

            packages = with pkgs."python${pyVersion}Packages"; [
              pytest-lsp
            ];
          }
      )
    );
  };
}
