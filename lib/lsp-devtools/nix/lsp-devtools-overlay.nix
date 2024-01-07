final: prev:

let
  # Read the package's version from file
  lines = prev.lib.splitString "\n" (builtins.readFile ../lsp_devtools/__init__.py);
  matches = builtins.map (builtins.match ''__version__ = "(.+)"'') lines;
  versionStr = prev.lib.concatStrings (prev.lib.flatten (builtins.filter builtins.isList matches));
in {
  pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [(
    python-final: python-prev: {

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
