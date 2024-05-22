import sys

import pytest
import pytest_lsp
from lsprotocol.types import (
    TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS,
    ClientCapabilities,
    DidOpenTextDocumentParams,
    InitializeParams,
    TextDocumentItem,
)
from pytest_lsp import ClientServerConfig, LanguageClient


@pytest_lsp.fixture(
    config=ClientServerConfig(server_command=[sys.executable, "server.py"]),
)
async def client(lsp_client: LanguageClient):
    # Setup
    params = InitializeParams(capabilities=ClientCapabilities())
    await lsp_client.initialize_session(params)

    yield

    # Teardown
    await lsp_client.shutdown_session()


@pytest.mark.asyncio
async def test_diagnostics(client: LanguageClient):
    """Ensure that the server implements diagnostics correctly."""

    test_uri = "file:///path/to/file.txt"
    client.text_document_did_open(
        DidOpenTextDocumentParams(
            text_document=TextDocumentItem(
                uri=test_uri,
                language_id="plaintext",
                version=1,
                text="The file's contents",
            )
        )
    )

    # Wait for the server to publish its diagnostics
    await client.wait_for_notification(TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)

    assert test_uri in client.diagnostics
    assert client.diagnostics[test_uri][0].message == "There is an error here."
