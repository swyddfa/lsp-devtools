import itertools
import json
import pathlib
import sys

import pygls.uris as uri
import pytest

import pytest_lsp


@pytest.mark.parametrize(
    "client_spec,capabilities",
    [
        *itertools.product(
            ["visual_studio_code", "visual-studio-code"],
            ["visual_studio_code_v1.65.2.json"],
        ),
        *itertools.product(
            ["neovim@0.6", "neovim@v0.6", "neovim@0.6.1"],
            ["neovim_v0.6.1.json"],
        ),
        *itertools.product(
            ["neovim", "neovim@latest", "neovim@v0", "neovim@v0.9", "neovim@v0.9.1"],
            ["neovim_v0.9.1.json"],
        ),
    ],
)
def test_client_capabilities(
    pytester: pytest.Pytester, client_spec: str, capabilities: str
):
    """Ensure that the plugin can mimic the requested client's capabilities correctly.

    Parameters
    ----------
    pytester
       pytest's built in pytester fixture.

    client_spec
       The string used to select the desired client and version

    client_capabilities
       The filename containing the expected client capabilities
    """

    python = sys.executable
    testdir = pathlib.Path(__file__).parent
    server = testdir / "servers" / "capabilities.py"
    root_uri = uri.from_fs_path(str(testdir))

    clients_dir = pathlib.Path(pytest_lsp.__file__).parent / "clients"
    with (clients_dir / capabilities).open() as f:
        # Easiest way to reformat the JSON onto a single line
        expected = json.dumps(json.load(f)["capabilities"])

    pytester.makeini(
        """
        [pytest]
        asyncio_mode = auto
        """
    )

    pytester.makeconftest(
        f"""
from lsprotocol.types import InitializeParams

import pytest_lsp
from pytest_lsp import ClientServerConfig
from pytest_lsp import LanguageClient
from pytest_lsp import client_capabilities

@pytest_lsp.fixture(
    config=ClientServerConfig(
        server_command=[r"{python}", r"{server}"],
    )
)
async def client(lsp_client: LanguageClient):
    await lsp_client.initialize_session(
        InitializeParams(
            capabilities=client_capabilities("{client_spec}"),
            root_uri=r"{root_uri}"
        )
    )
    yield

    await lsp_client.shutdown_session()
    """
    )

    pytester.makepyfile(
        f"""
import json
import pytest
from lsprotocol import types
from lsprotocol.converters import get_converter

@pytest.mark.asyncio
async def test_capabilities(client):
    actual = await client.workspace_execute_command_async(
        types.ExecuteCommandParams(command="return.client.capabilities")
    )

    expected = json.loads('{expected}')

    # lsprotocol is going to filter out any quirks of the client
    # so we can't compare the dicts directly.
    converter = get_converter()
    actual_capabilities = converter.structure(actual, types.ClientCapabilities)
    expected_capabilities = converter.structure(expected, types.ClientCapabilities)
    assert actual_capabilities == expected_capabilities
    """
    )

    results = pytester.runpytest("-vv")
    results.assert_outcomes(passed=1)
