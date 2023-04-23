import itertools
import json
import pathlib
import sys

import pygls.uris as uri
import pytest

import pytest_lsp


@pytest.mark.parametrize(
    "client_spec,client_capabilities",
    [
        *itertools.product(
            ["visual_studio_code", "visual-studio-code"],
            ["visual_studio_code_v1.65.2.json"],
        ),
        ("neovim", "neovim_v0.6.1.json"),
    ],
)
def test_client_capabilities(
    pytester: pytest.Pytester, client_spec: str, client_capabilities: str
):
    """Ensure that the plugin can mimic the requested client's capabilities."""

    python = sys.executable
    testdir = pathlib.Path(__file__).parent
    server = testdir / "servers" / "capabilities.py"
    root_uri = uri.from_fs_path(str(testdir))

    clients_dir = pathlib.Path(pytest_lsp.__file__).parent / "clients"
    with (clients_dir / client_capabilities).open() as f:
        # Easiest way to reformat the JSON onto a single line
        expected = json.dumps(json.load(f))

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
        server_command=["{python}", "{server}"],
    )
)
async def client(lsp_client: LanguageClient):
    await lsp_client.initialize_session(
        InitializeParams(
            capabilities=client_capabilities("{client_spec}"),
            root_uri="{root_uri}"
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
from lsprotocol.types import ExecuteCommandParams

@pytest.mark.asyncio
async def test_capabilities(client):
    actual = await client.workspace_execute_command_async(
        ExecuteCommandParams(command="return.client.capabilities")
    )
    assert actual == json.loads('{expected}')
    """
    )

    results = pytester.runpytest("-vv")
    results.assert_outcomes(passed=1)
