import sys

import pytest
from lsprotocol import types

import pytest_lsp
from pytest_lsp import ClientServerConfig
from pytest_lsp import LanguageClient


@pytest_lsp.fixture(
    scope="module",
    config=ClientServerConfig(server_command=[sys.executable, "server.py"]),
)
async def client(lsp_client: LanguageClient):
    # Setup
    params = types.InitializeParams(capabilities=types.ClientCapabilities())
    await lsp_client.initialize_session(params)

    yield

    # Teardown
    await lsp_client.shutdown_session()


@pytest.mark.asyncio(scope="module")
async def test_completion_hello(client: LanguageClient):
    """Ensure that the server implements completions correctly."""

    results = await client.text_document_completion_async(
        params=types.CompletionParams(
            position=types.Position(line=1, character=0),
            text_document=types.TextDocumentIdentifier(uri="file:///path/to/file.txt"),
        )
    )
    assert results is not None

    if isinstance(results, types.CompletionList):
        items = results.items
    else:
        items = results

    labels = {item.label for item in items}
    assert "hello" in labels


@pytest.mark.asyncio(scope="module")
async def test_completion_world(client: LanguageClient):
    """Ensure that the server implements completions correctly."""

    results = await client.text_document_completion_async(
        params=types.CompletionParams(
            position=types.Position(line=1, character=0),
            text_document=types.TextDocumentIdentifier(uri="file:///path/to/file.txt"),
        )
    )
    assert results is not None

    if isinstance(results, types.CompletionList):
        items = results.items
    else:
        items = results

    labels = {item.label for item in items}
    assert "world" in labels
