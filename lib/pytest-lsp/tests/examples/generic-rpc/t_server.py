import logging
import sys

import pytest
import pytest_lsp
from pygls.client import JsonRPCClient
from pytest_lsp import ClientServerConfig


def client_factory():
    client = JsonRPCClient()

    @client.feature("log/message")
    def _on_message(params):
        logging.info("LOG: %s", params.message)

    return client


@pytest_lsp.fixture(
    config=ClientServerConfig(
        client_factory=client_factory, server_command=[sys.executable, "server.py"]
    ),
)
async def client(rpc_client: JsonRPCClient):
    # Setup code here (if any)

    yield

    # Teardown code here (if any)


@pytest.mark.asyncio
async def test_add(client: JsonRPCClient):
    """Ensure that the server implements addition correctly."""

    result = await client.protocol.send_request_async(
        "math/add", params={"a": 1, "b": 2}
    )
    assert result.total == 3


@pytest.mark.asyncio
async def test_sub(client: JsonRPCClient):
    """Ensure that the server implements addition correctly."""

    result = await client.protocol.send_request_async(
        "math/sub", params={"a": 1, "b": 2}
    )
    assert result.total == -1
