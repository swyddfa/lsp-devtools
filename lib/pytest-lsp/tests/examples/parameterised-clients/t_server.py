import sys

from lsprotocol.types import InitializeParams

import pytest_lsp
from pytest_lsp import ClientServerConfig
from pytest_lsp import LanguageClient
from pytest_lsp import client_capabilities


@pytest_lsp.fixture(
    params=["neovim", "visual_studio_code"],
    config=ClientServerConfig(server_command=[sys.executable, "server.py"]),
)
async def client(request, lsp_client: LanguageClient):
    # Setup
    params = InitializeParams(capabilities=client_capabilities(request.param))
    await lsp_client.initialize(params)

    yield

    # Teardown
    await lsp_client.shutdown()


async def test_completions(client: LanguageClient):
    """Ensure that the server implements completions correctly."""

    results = await client.completion_request(
        uri="file:///path/to/file.txt", line=1, character=0
    )

    labels = [item.label for item in results]
    assert labels == ["hello", "world"]
