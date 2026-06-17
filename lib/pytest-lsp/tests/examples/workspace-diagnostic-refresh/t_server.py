import sys

import pytest
from lsprotocol import types

import pytest_lsp
from pytest_lsp import ClientServerConfig, LanguageClient


@pytest_lsp.fixture(
    config=ClientServerConfig(server_command=[sys.executable, "server.py"]),
)
async def client(lsp_client: LanguageClient):
    # Setup
    params = types.InitializeParams(
        capabilities=types.ClientCapabilities(
            workspace=types.WorkspaceClientCapabilities(configuration=False)
        )
    )
    await lsp_client.initialize_session(params)

    yield

    # Teardown
    await lsp_client.shutdown_session()


@pytest.mark.asyncio
async def test_diagnostic_refresh(client: LanguageClient):
    _ = await client.workspace_execute_command_async(
        params=types.ExecuteCommandParams(
            command="server.diagnostics", arguments=[False]
        )
    )
    assert client.diagnostic_refresh_count == 0

    _ = await client.workspace_execute_command_async(
        params=types.ExecuteCommandParams(
            command="server.diagnostics", arguments=[True]
        )
    )
    assert client.diagnostic_refresh_count == 1
