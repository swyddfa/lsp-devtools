final: prev:

let
  # Read the package's version from file
  lines = prev.lib.splitString "\n" (builtins.readFile ../pytest_lsp/client.py);
  matches = builtins.map (builtins.match ''__version__ = "(.+)"'') lines;
  versionStr = prev.lib.concatStrings (prev.lib.flatten (builtins.filter builtins.isList matches));
in {
  pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [(
    python-final: python-prev: {

      pytest-lsp = python-prev.buildPythonPackage {
        pname = "pytest-lsp";
        version = versionStr;
        format = "pyproject";

        src = ./..;

        nativeBuildInputs = with python-final; [
          hatchling
        ];

        propagatedBuildInputs = with python-final; [
          pygls
          pytest
          pytest-asyncio
        ];

        doCheck = true;
        pythonImportsCheck = [ "pytest_lsp" ];
        nativeCheckInputs = with python-prev; [
          pytestCheckHook
        ];

      };
    }
  )];
}
