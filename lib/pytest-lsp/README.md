# pytest-lsp: End-to-end testing of language servers with pytest

`pytest-lsp` is a pytest plugin for writing end-to-end tests for language servers.

It works by running the language server in a subprocess and communicating with it over stdio, just like a real language client.
This also means `pytest-lsp` can be used to test language servers written in any language - not just Python.

`pytest-lsp` relies on the [`pygls`](https://github.com/openlawlibrary/pygls) library for its language server protocol implementation.

See the [documentation](https://lsp-devtools.readthedocs.io/en/latest/) for details on getting started.

```python
import sys

import pytest_lsp
from lsprotocol.types import (
    CompletionParams,
    InitializeParams,
    Position,
    TextDocumentIdentifier,
)
from pytest_lsp import (
    ClientServerConfig,
    LanguageClient,
    client_capabilities,
)


@pytest_lsp.fixture(
    config=ClientServerConfig(
        server_command=[sys.executable, "-m", "esbonio"],
    ),
)
async def client(lsp_client: LanguageClient):
    # Setup
    response = await lsp_client.initialize_session(
        InitializeParams(
            capabilities=client_capabilities("visual-studio-code"),
            root_uri="file:///path/to/test/project/root/",
        )
    )

    yield

    # Teardown
    await lsp_client.shutdown_session()


async def test_completion(client: LanguageClient):
    result = await client.text_document_completion_async(
        params=CompletionParams(
            position=Position(line=5, character=23),
            text_document=TextDocumentIdentifier(
                uri="file:///path/to/test/project/root/test_file.rst"
            ),
        )
    )

    assert len(result.items) > 0
```
