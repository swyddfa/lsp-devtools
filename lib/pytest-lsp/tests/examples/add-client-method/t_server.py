import asyncio
import sys

import pytest
import pytest_lsp
from lsprotocol import types
from pytest_lsp import ClientServerConfig, LanguageClient


@pytest_lsp.fixture(
    config=ClientServerConfig(server_command=[sys.executable, "server.py"]),
)
async def client(lsp_client: LanguageClient):
    # Register a custom `workspace/diagnostic/refresh` implementation
    lsp_client.refresh_requests = 0

    @lsp_client.feature(types.WORKSPACE_DIAGNOSTIC_REFRESH)
    def refresh(cl: LanguageClient, params: None):
        cl.refresh_requests += 1

    # Setup
    await lsp_client.initialize_session(
        types.InitializeParams(capabilities=types.ClientCapabilities())
    )

    yield

    # Teardown
    await lsp_client.shutdown_session()


@pytest.mark.asyncio
async def test_did_open(client: LanguageClient):
    """Ensure that the server requests a diagnostic refresh when a file is opened."""
    client.text_document_did_open(
        params=types.DidOpenTextDocumentParams(
            text_document=types.TextDocumentItem(
                uri="file:///path/to/file.txt",
                language_id="plaintext",
                version=1,
                text="Hello, world!\n",
            ),
        )
    )

    # Give the server time to process...
    await asyncio.sleep(1)
    assert client.refresh_requests == 1
