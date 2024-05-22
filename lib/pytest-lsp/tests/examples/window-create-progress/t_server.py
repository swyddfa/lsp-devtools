import sys

import pytest
import pytest_lsp
from lsprotocol import types
from pytest_lsp import ClientServerConfig, LanguageClient, LspSpecificationWarning


@pytest_lsp.fixture(
    config=ClientServerConfig(server_command=[sys.executable, "server.py"]),
)
async def client(lsp_client: LanguageClient):
    # Setup
    params = types.InitializeParams(capabilities=types.ClientCapabilities())
    await lsp_client.initialize_session(params)

    yield

    # Teardown
    await lsp_client.shutdown_session()


@pytest.mark.asyncio
async def test_progress(client: LanguageClient):
    result = await client.workspace_execute_command_async(
        params=types.ExecuteCommandParams(command="do.progress")
    )

    assert result == "a result"

    progress = client.progress_reports["a-token"]
    assert progress == [
        types.WorkDoneProgressBegin(title="Indexing", percentage=0),
        types.WorkDoneProgressReport(message="25%", percentage=25),
        types.WorkDoneProgressReport(message="50%", percentage=50),
        types.WorkDoneProgressReport(message="75%", percentage=75),
        types.WorkDoneProgressEnd(message="Finished"),
    ]


@pytest.mark.asyncio
async def test_duplicate_progress(client: LanguageClient):
    with pytest.warns(
        LspSpecificationWarning, match="Duplicate progress token: 'duplicate-token'"
    ):
        await client.workspace_execute_command_async(
            params=types.ExecuteCommandParams(command="duplicate.progress")
        )


@pytest.mark.asyncio
async def test_unknown_progress(client: LanguageClient):
    with pytest.warns(
        LspSpecificationWarning, match="Unknown progress token: 'undefined-token'"
    ):
        await client.workspace_execute_command_async(
            params=types.ExecuteCommandParams(command="no.progress")
        )
