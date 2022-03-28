# Clients

This folder contains recorded `ClientCapabilities` responses from various language clients at various versions.

These snapshots is how the `pytest-lsp` plugin is able to simulate different language clients when testing a language server.

## Adding new clients/versions

Adding support for a new client requires the client's `ClientCapabilities` response being captured in a JSON file and stored in this folder.
The simplest way to generate the required JSON file is to use the `lsp-devtools capabilities` command.

1. Configure the language client to call the `lsp-devtools capabilities` command as if it were a language server.
1. Run the language client as configured to generate a `ClientCapabilites` response.
1. A file called `<client_name>_v<client_version>.json` should appear in you working directory, copy-paste it into this folder.

New versions of a client should only be added if there is a noticable difference in the `ClientCapabilities` response when compared to previous versions..

