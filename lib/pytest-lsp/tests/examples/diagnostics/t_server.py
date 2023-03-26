import sys

from lsprotocol.types import TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS
from lsprotocol.types import ClientCapabilities
from lsprotocol.types import InitializeParams

import pytest_lsp
from pytest_lsp.client import LanguageClient
from pytest_lsp.plugin import ClientServerConfig


@pytest_lsp.fixture(
    config=ClientServerConfig(server_command=[sys.executable, "server.py"]),
)
async def client(lsp_client: LanguageClient):
    # Setup
    params = InitializeParams(capabilities=ClientCapabilities())
    await lsp_client.initialize(params)

    yield

    # Teardown
    await lsp_client.shutdown()


async def test_diagnostics(client: LanguageClient):
    """Ensure that the server implements diagnostics correctly."""

    test_uri = "file:///path/to/file.txt"
    client.notify_did_open(
        uri=test_uri, language="plaintext", contents="The file's contents"
    )

    # Wait for the server to publish its diagnostics
    await client.wait_for_notification(TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)

    assert test_uri in client.diagnostics
    assert client.diagnostics[test_uri][0].message == "There is an error here."
