import sys

import pytest
import pytest_lsp
from lsprotocol import types
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
async def test_configuration(client: LanguageClient):
    global_config = {"values": {"a": 42, "c": 4}}

    workspace_uri = "file://workspace/file.txt"
    workspace_config = {"a": 1, "c": 1}

    client.set_configuration(global_config)
    client.set_configuration(
        workspace_config, section="values", scope_uri=workspace_uri
    )

    result = await client.workspace_execute_command_async(
        params=types.ExecuteCommandParams(command="server.configuration")
    )
    assert result == 5
