import pathlib
import sys

import pygls.uris as uri
import pytest


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
        server_command=["{python}", "{server}"],
    )
)
async def client(lsp_client: LanguageClient):
    await lsp_client.initialize_session(
        InitializeParams(
            capabilities=client_capabilities("visual-studio-code"),
            root_uri="{root_uri}"
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

    if sys.version_info.minor < 9:
        message = "E*CancelledError"
    else:
        message = "E*asyncio.exceptions.CancelledError: RuntimeError: Server exited with return code: 0"  # noqa: E501

    results.stdout.fnmatch_lines(message)


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

    results.assert_outcomes(failed=1)

    if sys.version_info.minor < 9:
        message = "E*CancelledError"
    else:
        message = "E*asyncio.exceptions.CancelledError: RuntimeError: Server exited with return code: 0"  # noqa: E501

    results.stdout.fnmatch_lines(message)


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

    if sys.version_info.minor < 9:
        message = "E*CancelledError"
    else:
        message = [
            "E*asyncio.exceptions.CancelledError: RuntimeError: Server exited with return code: 1",  # noqa: E501
            "E*ZeroDivisionError: division by zero",
        ]

    results.stdout.fnmatch_lines(message)


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

    if sys.version_info.minor < 9:
        message = "E*CancelledError"
    else:
        message = "E*asyncio.exceptions.CancelledError: JsonRpcInternalError: *"

    results.stdout.fnmatch_lines(message)
