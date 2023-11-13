# lsp-devtools: Developer tooling for language servers

This package provides a collection of cli utilities to support the development of language servers.
While this is a Python package, it can be used with language servers written in any langauge.

![lsp-devtools client](https://user-images.githubusercontent.com/2675694/273293510-e43fdc92-03dd-40c9-aaca-ddb5e526031a.png)

Available commands:

- `agent`: Wrap a language server allowing other commands to access the messages sent to and from the client
- `client`: **Experimental** a language client with an embedded inspector. Powered by [textual](https://textual.textualize.io/)
- `record`: Connects to an agent and record traffic to file, sqlite db or console. Supports filtering and formatting the output
- `inspect`: A text user interface to visualise and inspect LSP traffic. Powered by [textual](https://textual.textualize.io/)

See the [documentation](https://lsp-devtools.readthedocs.io/en/latest/) for more information

## Installation

Install using [pipx](https://pypa.github.io/pipx/)

```
pipx install lsp-devtools
```
