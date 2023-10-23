from typing import Any

import pytest
from lsprotocol import types

from pytest_lsp import checks


@pytest.mark.parametrize(
    "capabilities,method,params,expected",
    [
        (
            types.ClientCapabilities(
                workspace=types.WorkspaceClientCapabilities(configuration=False)
            ),
            types.WORKSPACE_CONFIGURATION,
            types.WorkspaceConfigurationParams(items=[]),
            "does not support 'workspace/configuration'",
        ),
    ],
)
def test_params_check_warning(
    capabilities: types.ClientCapabilities, method: str, params: Any, expected: str
):
    """Ensure that parameter checks work as expected.

    Parameters
    ----------
    capabilities
       The client's capabilities

    method
       The method name to check

    params
       The params to check

    expected
       The expected warning message
    """

    with pytest.warns(checks.LspSpecificationWarning, match=expected):
        checks.check_params_against_client_capabilities(capabilities, method, params)
