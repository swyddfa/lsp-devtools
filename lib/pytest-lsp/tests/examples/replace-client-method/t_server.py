import asyncio
import sys

import pytest
import pytest_lsp
from lsprotocol import types
from pytest_lsp import ClientServerConfig, LanguageClient


def disallow_publish_diagnostics(
    client: LanguageClient, params: types.PublishDiagnosticsParams
):
    """Raises an error if the server calls ``textDocument/publishDiagnostics``"""
    raise RuntimeError("The server should not use `textDocument/publishDiagnostics`")


# Putting this here so the code example in the docs includes the imports
from pygls.protocol import default_converter
from pytest_lsp.client import DEFAULT_CLIENT_FEATURES, register_lsp_features


def my_make_test_lsp_client() -> LanguageClient:
    """Return a customised ``LanguageClient`` instance"""
    client = LanguageClient(
        converter_factory=default_converter,
    )

    features = {
        **DEFAULT_CLIENT_FEATURES,
        types.TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS: disallow_publish_diagnostics,
    }

    register_lsp_features(client, features)
    return client


@pytest_lsp.fixture(
    config=ClientServerConfig(
        client_factory=my_make_test_lsp_client,
        server_command=[sys.executable, "server.py"],
    ),
)
async def client(lsp_client: LanguageClient):
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
