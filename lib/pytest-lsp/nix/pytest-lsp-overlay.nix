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

      lsprotocol = python-prev.lsprotocol.overridePythonAttrs(oldAttrs: rec {
        version = "2023.0.0a3";

        src = prev.fetchFromGitHub {
          rev = version;
          owner = "microsoft";
          repo = oldAttrs.pname;
          sha256 = "sha256-Q4jvUIMMaDX8mvdmRtYKHB2XbMEchygO2NMmMQdNkTc=";
        };
      });

      pygls = python-prev.pygls.overridePythonAttrs (_: {
        format = "pyproject";

        src = prev.fetchFromGitHub {
          owner = "openlawlibrary";
          repo = "pygls";
          rev = "main";
          hash = "sha256-JpopfqeLNi23TuZ5mkPEShUPScd1fB0IDXSVGvDYFXE=";
        };

        nativeBuildInputs = with python-prev; [
          poetry-core
        ];
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
