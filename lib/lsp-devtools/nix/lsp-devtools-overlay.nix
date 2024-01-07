final: prev:

let
  # Read the package's version from file
  lines = prev.lib.splitString "\n" (builtins.readFile ../lsp_devtools/__init__.py);
  matches = builtins.map (builtins.match ''__version__ = "(.+)"'') lines;
  versionStr = prev.lib.concatStrings (prev.lib.flatten (builtins.filter builtins.isList matches));
in {
  pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [(
    python-final: python-prev: {

      stamina = python-prev.buildPythonPackage rec {
        pname = "stamina";
        version = "24.1.0";
        format = "pyproject";

        src = prev.fetchFromGitHub {
          owner = "hynek";
          repo = "stamina";
          rev = "refs/tags/${version}";
          hash = "sha256-bIVzE9/QsdGw/UE83q3Q/XG3jFnPy65pkDdMpYkIrrs=";
        };

        SETUPTOOLS_SCM_PRETEND_VERSION = version;
        nativeBuildInputs = with python-final; [
          hatchling
          hatch-vcs
          hatch-fancy-pypi-readme
        ];

        propagatedBuildInputs = with python-final; [
          tenacity
        ] ++ prev.lib.optional (pythonOlder "3.10") typing-extensions;

        doCheck = true;
        pythonImportsCheck = [ "stamina" ];
        nativeCheckInputs = with python-prev; [
          anyio
          pytestCheckHook
        ];

      };

      lsp-devtools = python-prev.buildPythonPackage {
        pname = "lsp-devtools";
        version = versionStr;
        format = "pyproject";

        src = ./..;

        nativeBuildInputs = with python-final; [
          hatchling
        ];

        propagatedBuildInputs = with python-final; [
          aiosqlite
          platformdirs
          pygls
          stamina
          textual
        ] ++ prev.lib.optional (pythonOlder "3.9") importlib-resources
          ++ prev.lib.optional (pythonOlder "3.8") typing-extensions;

        doCheck = true;
        pythonImportsCheck = [ "lsp_devtools" ];
        nativeCheckInputs = with python-prev; [
          pytestCheckHook
        ];

      };
    }
  )];
}
