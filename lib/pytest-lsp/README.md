# pytest-lsp: End-to-end testing of language servers with pytest

`pytest-lsp` is a pytest plugin for writing end-to-end tests for language servers.

It works by running the language server in a subprocess and communicating with it over stdio, just like a real language client.
This also means `pytest-lsp` can be used to test language servers written in any language - not just Python.

`pytest-lsp` relies on the [`pygls`](https://github.com/openlawlibrary/pygls) library for its language server protocol implementation.

```python
import sys

import pytest_lsp
from lsprotocol.types import InitializeParams
from pytest_lsp import ClientServerConfig, LanguageClient, client_capabilities


@pytest_lsp.fixture(
    config=ClientServerConfig(
        server_command=[sys.executable, "-m", "esbonio"],
    ),
)
async def client(lsp_client: LanguageClient):
    # Setup
    response = await lsp_client.initialize(
        InitializeParams(
            capabilities=client_capabilities("visual-studio-code")
            root_uri="file:///path/to/test/project/root/",
        )
    )

    yield

    # Teardown
    await lsp_client.shutdown()


async def test_completion(client: LanguageClient):
    test_uri="file:///path/to/test/project/root/test_file.rst"
    result = await client.completion_request(test_uri, line=5, character=23)

    assert len(result.items) > 0
```
