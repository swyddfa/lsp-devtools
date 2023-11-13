# Clients

This folder contains captured [`ClientCapabilities`](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#clientCapabilities) responses from various language clients at various versions.

These snapshots are how `pytest-lsp` plugin is able to impersonate different language clients when testing a server.
They also power the [Client Capability Index](https://lsp-devtools.readthedocs.io/en/latest/#client-capability-index) section of the documentation.

Each filename follows the `<client_name>_v<client_version>.json` naming convention and contain the following fields of an [`InitializeParams`](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#initializeParams) object.

```json
{
  "clientInfo": {
    "name": "Client Name",
    "version": "1.2.3"
  },
  "capabilities": { ... }
}
```

## Adding new clients and versions

### Neovim

Adding new neovim versions has been semi-automated through a [Github Actions workflow](https://github.com/swyddfa/lsp-devtools/blob/develop/.github/workflows/capabilities-nvim.yml)

### Other Clients

This can be done with `lsp-devtools` command.

1. Configure the language client to invoke a language server [wrapped with the lsp-devtools agent](https://lsp-devtools.readthedocs.io/en/latest/lsp-devtools/guide/getting-started.html#configuring-your-client).

1. In a separate terminal, use the following `lsp-devtools` command to record the necessary information to a JSON file
   ```
   lsp-devtools record -f '{{"clientInfo": {.params.clientInfo}, "capabilities": {.params.capabilities}}}' --to-file <client_name>_v<version>.json
   ```

1. Run the language server via the client to generate the necessary data, once the server is ready to use you should be able to close the client.

1. The `lsp-devtools record` command should have exited with a file called `<client_name>_v<client_version>.json` saved to your working directory.

1. Open a pull request adding the file to this folder!
