import sys

from lsprotocol.types import ClientCapabilities
from lsprotocol.types import CompletionList
from lsprotocol.types import CompletionParams
from lsprotocol.types import InitializeParams
from lsprotocol.types import Position
from lsprotocol.types import TextDocumentIdentifier

import pytest
import pytest_lsp
from pytest_lsp import ClientServerConfig
from pytest_lsp import LanguageClient


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
    assert labels == ["hello", "world"]
