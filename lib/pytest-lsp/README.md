# pytest-lsp: End-to-end testing of language servers with pytest

`pytest-lsp` is a pytest plugin for writing end-to-end tests for language servers.

It works by running the language server in a subprocess and communicating with it over stdio, just like a real language client.
This also means `pytest-lsp` can be used to test language servers written in any language - not just Python.

`pytest-lsp` relies on the [`pygls`](https://github.com/openlawlibrary/pygls) library for its language server protocol implementation.

See the [documentation](https://lsp-devtools.readthedocs.io/en/latest/) for details on getting started.

```python
import sys

import pytest
import pytest_lsp
from lsprotocol import types
from pytest_lsp import (
    ClientServerConfig,
    LanguageClient,
    client_capabilities,
)


@pytest_lsp.fixture(
    scope="module",
    config=ClientServerConfig(
        server_command=[sys.executable, "-m", "esbonio"],
    ),
)
async def client(lsp_client: LanguageClient):
    # Setup
    response = await lsp_client.initialize_session(
        types.InitializeParams(
            capabilities=client_capabilities("visual-studio-code"),
            workspace_folders=[
                types.WorkspaceFolder(
                    uri="file:///path/to/test/project/root/", name="project"
                ),
            ],
        )
    )

    yield

    # Teardown
    await lsp_client.shutdown_session()


@pytest.mark.asyncio(loop_scope="module")
async def test_completion(client: LanguageClient):
    result = await client.text_document_completion_async(
        params=types.CompletionParams(
            position=types.Position(line=5, character=23),
            text_document=types.TextDocumentIdentifier(
                uri="file:///path/to/test/project/root/test_file.rst"
            ),
        )
    )

    assert len(result.items) > 0
```
