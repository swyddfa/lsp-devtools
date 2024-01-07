final: prev: {
  pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [(
    python-final: python-prev: {

      pytest-lsp = python-prev.buildPythonPackage {
        pname = "pytest-lsp";
        version = "0.3.0";
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
