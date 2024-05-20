import itertools
import json
import pathlib
import sys
from typing import Any
from typing import Dict
from typing import Optional

import pygls.uris as uri
import pytest

import pytest_lsp
from pytest_lsp import LanguageClient


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
            ["neovim", "neovim@latest", "neovim@v0", "neovim@v0.10", "neovim@v0.10.0"],
            ["neovim_v0.10.0.json"],
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


@pytest.mark.parametrize(
    "config,section,scope,expected",
    [
        ({"": 12}, None, None, 12),
        ({"": 12}, "example.section", None, None),
        ({"": 12}, None, "file://path/to/workspace/file.txt", 12),
        ({"": {"example": {"section": 12}}}, "example", None, {"section": 12}),
        ({"": {"example": {"section": 12}}}, "example.section", None, 12),
        (
            {"": {"example": {"section": 12}}},
            "example.section",
            "file://path/to/workspace/file.txt",
            12,
        ),
        (
            {
                "": {"example": {"section": 12}},
                "file://path/to/workspace": {"example": {"section": 32}},
            },
            "example.section",
            "file://path/to/workspace/file.txt",
            32,
        ),
        # To keep things simple, we will not try to fallback to more general scopes.
        (
            {
                "": {"example": {"section": 12}},
                "file://path/to/workspace": {"example": 32},
            },
            "example.section",
            "file://path/to/workspace/file.txt",
            None,
        ),
    ],
)
def test_get_configuration(
    config: Dict[str, Any], section: Optional[str], scope: Optional[str], expected: Any
):
    """Ensure that we can get a client's configuration correctly.

    Parameters
    ----------
    config
       The client's configuration

    section
       The section name to retrieve

    scope
       The scope to retrieve

    expected
       The expected result
    """

    client = LanguageClient(configuration=config)
    assert client.get_configuration(section=section, scope_uri=scope) == expected


@pytest.mark.parametrize(
    "item,section,scope,expected",
    [
        (12, None, None, {"": 12}),
        (
            12,
            None,
            "file://path/to/workspace",
            {"": {}, "file://path/to/workspace": 12},
        ),
        (12, "example", None, {"": {"example": 12}}),
        (
            12,
            "example.config.section",
            None,
            {"": {"example": {"config": {"section": 12}}}},
        ),
    ],
)
def test_set_configuration(
    item: Any, section: Optional[str], scope: Optional[str], expected: Dict[str, Any]
):
    """Ensure that we can set the client's configuration correctly.

    Parameters
    ----------
    item
       The value to set

    section
       The configuration section to set

    scope
       The scope at which to set the configuration

    expected
       The expected result
    """
    client = LanguageClient()
    client.set_configuration(item, section=section, scope_uri=scope)

    assert client._configuration == expected


def test_set_configuration_equivalent_methods():
    """Ensure that setting the configuration using alternate, but equivalent methods
    yields the same result."""

    client_one = LanguageClient()
    client_two = LanguageClient()

    config = {
        "example": {
            "section": 12,
            "value": "test",
            "nested": {"section": 34},
        },
    }
    client_one.set_configuration(config)

    client_two.set_configuration(12, section="example.section")
    client_two.set_configuration("test", section="example.value")
    client_two.set_configuration(34, section="example.nested.section")

    expected = {
        "": {
            "example": {
                "section": 12,
                "value": "test",
                "nested": {"section": 34},
            },
        },
    }
    assert client_one._configuration == expected == client_two._configuration
