<h1 align="center">LSP Devtools</h1>

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/swyddfa/lsp-devtools/develop.svg)](https://results.pre-commit.ci/latest/github/swyddfa/lsp-devtools/develop)

This repo is an attempt at building the developer tooling I wished existed when I first started working on [Esbonio](https://github.com/swyddfa/esbonio/).

**Everything here is early in its development, so expect plenty of bugs and missing features.**

This is a monorepo containing a number of sub-projects.

## `lib/lsp-devtools` - A grab bag of development utilities

[![PyPI](https://img.shields.io/pypi/v/lsp-devtools?style=flat-square)](https://pypi.org/project/lsp-devtools)[![PyPI - Downloads](https://img.shields.io/pypi/dm/lsp-devtools?style=flat-square)](https://pypistats.org/packages/lsp-devtools)[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)](https://github.com/swyddfa/lsp-devtools/blob/develop/lib/lsp-devtools/LICENSE)

![TUI Screenshot](https://user-images.githubusercontent.com/2675694/212438877-d332dd84-14b4-4568-b36f-4c3e04d4f95f.png)

A collection of cli utilities aimed at aiding the development of language servers and/or clients.

- `agent`: Used to wrap an lsp server allowing messages sent between it and the client to be intercepted and inspected by other tools.
- `record`: Connects to an agent and record traffic to file, sqlite db or console. Supports filtering and formatting the output
- `tui`: A text user interface to visualise and inspect LSP traffic. Powered by [textual](https://textual.textualize.io/)

## `lib/pytest-lsp` - End-to-end testing of language servers with pytest

[![PyPI](https://img.shields.io/pypi/v/pytest-lsp?style=flat-square)](https://pypi.org/project/pytest-lsp)[![PyPI - Downloads](https://img.shields.io/pypi/dm/pytest-lsp?style=flat-square)](https://pypistats.org/packages/pytest-lsp)[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)](https://github.com/swyddfa/lsp-devtools/blob/develop/lib/pytest-lsp/LICENSE)

`pytest-lsp` is a pytest plugin for writing end-to-end tests for language servers.

It works by running the language server in a subprocess and communicating with it over stdio, just like a real language client.
This also means `pytest-lsp` can be used to test language servers written in any language - not just Python.

`pytest-lsp` relies on the [`pygls`](https://github.com/openlawlibrary/pygls) library for its language server protocol implementation.

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

## `app/` - Prototype Devtools Web UI

![UI Screenshot](https://user-images.githubusercontent.com/2675694/191863035-5bb5d1c9-00b6-40de-b3e2-f81cdb9eb375.png)

This is little more than a proof of concept, currently setup to communicate with an agent over websockets.
Hopefully, this can eventually be repurposed/extended to be used on lsp servers hosted entirely in the browser e.g. pyodide.
