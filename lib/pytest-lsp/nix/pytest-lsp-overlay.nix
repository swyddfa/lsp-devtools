let
  doPythonOverride = version: f:
    let
      overridenPython = f version;
    in
      builtins.listToAttrs [ {name = "python${version}" ; value = overridenPython ; }
                             {name = "python${version}Packages" ; value = overridenPython.pkgs ; }];

  eachPythonVersion = versions: f: builtins.foldl' (a: b: a // b) {}
    (builtins.map (version: doPythonOverride version f) versions);
in

self: super:

eachPythonVersion [ "37" "38" "39" "310" "311" ] (pyVersion:
  super."python${pyVersion}".override {
    packageOverrides = pyself: pysuper: {

      pytest-lsp = pysuper.buildPythonPackage {
        pname = "pytest-lsp";
        version = "0.2.1";

        src = ./..;

        propagatedBuildInputs = with super."python${pyVersion}Packages"; [
          pygls
          pytest
          pytest-asyncio
        ];

      };
    };
})
