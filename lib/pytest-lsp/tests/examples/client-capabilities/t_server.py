import sys

import pytest_lsp
from lsprotocol.types import (
    CompletionList,
    CompletionParams,
    InitializeParams,
    Position,
    TextDocumentIdentifier,
)
from pytest_lsp import ClientServerConfig, LanguageClient, client_capabilities


@pytest_lsp.fixture(
    config=ClientServerConfig(server_command=[sys.executable, "server.py"]),
)
async def client(lsp_client: LanguageClient):
    # Setup
    await lsp_client.initialize_session(
        InitializeParams(
            capabilities=client_capabilities("neovim"),
        ),
    )

    yield

    # Teardown
    await lsp_client.shutdown_session()


async def test_completions(client: LanguageClient):
    """Ensure that the server implements completions correctly."""

    results = await client.text_document_completion_async(
        params=CompletionParams(
            position=Position(line=1, character=0),
            text_document=TextDocumentIdentifier(uri="file:///path/to/file.txt"),
        )
    )
    assert results is not None

    if isinstance(results, CompletionList):
        items = results.items
    else:
        items = results

    labels = [item.label for item in items]
    assert labels == ["greet"]
