import itertools
import json
import pathlib
import sys

import pytest
import pytest_lsp
import pygls.uris as uri


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
import pytest_lsp
from pytest_lsp import ClientServerConfig

@pytest_lsp.fixture(
    config=ClientServerConfig(
        client="{client_spec}",
        server_command=["{python}", "{server}"],
        root_uri="{root_uri}"
    )
)
async def client(client_):
    ...
    """
    )

    pytester.makepyfile(
        f"""
import json
import pytest

@pytest.mark.asyncio
async def test_capabilities(client):
    actual = await client.execute_command_request("return.client.capabilities") 
    assert actual == json.loads('{expected}')
    """
    )

    results = pytester.runpytest()
    results.assert_outcomes(passed=1)
