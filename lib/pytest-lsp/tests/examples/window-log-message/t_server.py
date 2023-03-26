import sys

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


async def test_completions(client: LanguageClient):
    test_uri = "file:///path/to/file.txt"
    results = await client.completion_request(uri=test_uri, line=1, character=0)

    labels = [item.label for item in results]
    assert labels == [f"item-{i}" for i in range(10)]

    for idx, log_message in enumerate(client.log_messages):
        assert log_message.message == f"Suggesting item {idx}"
