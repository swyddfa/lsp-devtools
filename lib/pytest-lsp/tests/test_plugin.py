import pathlib
import sys
from typing import Any
from typing import Dict
from typing import List

import pygls.uris as uri
import pytest

from pytest_lsp.plugin import ClientServerConfig


@pytest.mark.parametrize(
    "config, kwargs, expected",
    [
        (ClientServerConfig(server_command=["command"]), {}, ["command"]),
        (
            ClientServerConfig(server_command=["command"]),
            {"devtools": "1234"},
            [
                "lsp-devtools",
                "agent",
                "--host",
                "localhost",
                "--port",
                "1234",
                "--",
                "command",
            ],
        ),
        (
            ClientServerConfig(server_command=["command"]),
            {"devtools": "localhost:1234"},
            [
                "lsp-devtools",
                "agent",
                "--host",
                "localhost",
                "--port",
                "1234",
                "--",
                "command",
            ],
        ),
        (
            ClientServerConfig(server_command=["command"]),
            {"devtools": "127.0.0.1:1234"},
            [
                "lsp-devtools",
                "agent",
                "--host",
                "127.0.0.1",
                "--port",
                "1234",
                "--",
                "command",
            ],
        ),
    ],
)
def test_get_server_command(
    config: ClientServerConfig, kwargs: Dict[str, Any], expected: List[str]
):
    """Ensure that we can build the server start command correctly."""
    actual = config.get_server_command(**kwargs)
    assert expected == actual


def setup_test(pytester: pytest.Pytester, server_name: str, test_code: str):
    """Boilerplate for setting up a test."""

    python = sys.executable
    testdir = pathlib.Path(__file__).parent

    server = testdir / "servers" / server_name
    root_uri = uri.from_fs_path(str(testdir))

    pytester.makeini(
        """\
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
            capabilities=client_capabilities("visual-studio-code"),
            root_uri=r"{root_uri}"
        )
    )
    yield

    await lsp_client.shutdown_session()
    """
    )

    pytester.makepyfile(test_code)


def test_detect_server_exit(pytester: pytest.Pytester):
    """Ensure that the plugin can detect when the server process exits."""

    test_code = """\
import pytest

@pytest.mark.asyncio
async def test_capabilities(client):
    ...  # Test code does not matter in this case, as the error should be in the setup.
"""

    setup_test(pytester, "hello.py", test_code)
    results = pytester.runpytest("-vv")

    results.assert_outcomes(errors=1)

    message = r"E\s+RuntimeError: Server process \d+ exited with code: 0"
    results.stdout.re_match_lines(message)


def test_detect_server_exit_mid_request(pytester: pytest.Pytester):
    """Ensure that the plugin can detect when the server process exits mid request."""

    test_code = """\
import pytest
from lsprotocol.types import CompletionParams
from lsprotocol.types import Position
from lsprotocol.types import TextDocumentIdentifier


@pytest.mark.asyncio
async def test_capabilities(client):
    expected = {str(i) for i in range(10)}

    for i in range(10):
        params = CompletionParams(
            text_document=TextDocumentIdentifier(uri="file:///test.txt"),
            position=Position(line=0, character=0)
        )
        items = await client.text_document_completion_async(params)
        assert len({i.label for i in items} & expected) == len(items)
"""

    setup_test(pytester, "completion_exit.py", test_code)
    results = pytester.runpytest("-vv")

    results.assert_outcomes(failed=1, errors=1)

    message = r"E\s+RuntimeError: Server process \d+ exited with code: 0"
    results.stdout.re_match_lines(message)
    results.stdout.fnmatch_lines("E*RuntimeError: Client has been stopped.")


def test_detect_server_crash(pytester: pytest.Pytester):
    """Ensure the plugin can detect when the server process crashes on boot."""

    test_code = """\
import pytest

@pytest.mark.asyncio
async def test_capabilities(client):
    ... # Test code does not matter in this case, as the error should be in the setup.
"""

    setup_test(pytester, "crash.py", test_code)
    results = pytester.runpytest("-vv")

    results.assert_outcomes(errors=1)

    message = r"E\s+RuntimeError: Server process \d+ exited with code: 1"
    results.stdout.re_match_lines(message)
    results.stdout.fnmatch_lines("ZeroDivisionError: division by zero")


def test_detect_invalid_json(pytester: pytest.Pytester):
    """Ensure that the plugin can detect when the server sends bad JSON."""

    test_code = """\
import pytest
from lsprotocol.types import CompletionParams
from lsprotocol.types import Position
from lsprotocol.types import TextDocumentIdentifier


@pytest.mark.asyncio
async def test_capabilities(client):
    expected = {str(i) for i in range(10)}

    for i in range(10):
        items = await client.text_document_completion_async(
            CompletionParams(
                text_document=TextDocumentIdentifier(uri="file:///test.txt"),
                position=Position(line=0, character=0)
            )
        )
        assert len({i.label for i in items} & expected) == len(items)
"""

    setup_test(pytester, "invalid_json.py", test_code)
    results = pytester.runpytest("-vv")

    results.assert_outcomes(errors=1, failed=1)

    if sys.version_info < (3, 9):
        message = "E*CancelledError"
    else:
        message = "E*asyncio.exceptions.CancelledError: JsonRpcInternalError: *"

    results.stdout.fnmatch_lines(message)
