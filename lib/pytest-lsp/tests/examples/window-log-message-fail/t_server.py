import sys

import pytest
import pytest_lsp
from lsprotocol.types import (
    ClientCapabilities,
    CompletionList,
    CompletionParams,
    InitializeParams,
    Position,
    TextDocumentIdentifier,
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


async def test_completions(client: LanguageClient):
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
    assert labels == [f"item-{i}" for i in range(10)]

    for idx, log_message in enumerate(client.log_messages):
        assert log_message.message == f"Suggesting item {idx}"

    pytest.fail("Failing test!")  # Force the test case to fail.
