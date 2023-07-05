final: prev: {
  pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [(
    python-final: python-prev: {

      # TODO: Remove once https://github.com/NixOS/nixpkgs/pull/233870 is merged
      typeguard = python-prev.typeguard.overridePythonAttrs (oldAttrs: rec {
        version = "3.0.2";
        format = "pyproject";

        src = prev.fetchPypi {
          inherit version;
          pname = oldAttrs.pname;
          sha256 = "sha256-/uUpf9so+Onvy4FCte4hngI3VQnNd+qdJwta+CY1jVo=";
        };

        propagatedBuildInputs = with python-prev; [
          importlib-metadata
          typing-extensions
        ];

      });

      pygls = python-prev.pygls.overridePythonAttrs (_: {
        src = prev.fetchFromGitHub {
          owner = "openlawlibrary";
          repo = "pygls";
          rev = "main";
          hash = "sha256-KjnuGQy3/YBSZyXYNWz4foUsFRbinujGxCkQjRSK4PE=";
        };
      });

      pytest-lsp = python-prev.buildPythonPackage {
        pname = "pytest-lsp";
        version = "0.3.0";

        src = ./..;

        propagatedBuildInputs = with python-final; [
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
