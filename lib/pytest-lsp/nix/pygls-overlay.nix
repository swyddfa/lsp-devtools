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
      packageOverrides = pyself: pysuper: rec {

      lsprotocol = pysuper.buildPythonPackage rec {
        pname = "lsprotocol";
        version = "2022.0.0a9";
        format = "pyproject";

        src = super.fetchFromGitHub {
          owner = "microsoft";
          repo = pname;
          rev = version;
          hash = "sha256-6XecPKuBhwtkmZrGozzO+VEryI5wwy9hlvWE1oV6ajk=";
        };

        nativeBuildInputs = with super."python${pyVersion}Packages"; [
          flit-core
        ];

        propagatedBuildInputs = with super."python${pyVersion}Packages"; [
          cattrs
          attrs
        ];

        doCheck = false;
      };

      pygls = pysuper.pygls.overrideAttrs (_: rec {
        version = "1.0.0";
        SETUPTOOLS_SCM_PRETEND_VERSION = version;

        src = super.fetchFromGitHub {
          owner = "openlawlibrary";
          repo = "pygls";
          rev = "v${version}";
          hash = "sha256-31J4+giK1RDBS52Q/Ia3Y/Zak7fp7gRVTQ7US/eFjtM=";
        };

        propagatedBuildInputs = with self."python${pyVersion}Packages"; [
          lsprotocol
          typeguard
        ];

      });
    };
 })
