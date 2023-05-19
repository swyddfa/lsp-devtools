final: prev: {
  pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [(
    python-final: python-prev: {
      pytest-lsp = python-prev.buildPythonPackage {
        pname = "pytest-lsp";
        version = "0.2.1";

        src = ./..;

        propagatedBuildInputs = with python-prev; [
          pygls
          pytest
          pytest-asyncio
        ];

        doCheck = true;

        nativeCheckInputs = with python-prev; [
          pytestCheckHook
        ];

        pythonImportsCheck = [ "pytest_lsp" ];

      };
    }
  )];
}
