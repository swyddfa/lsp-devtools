# lsp-devtools: Developer tooling for language servers/clients

**This is in very early development.**

There are a few cli commands already

```
usage: lsp-devtools [-h] {capabilities,record} ...

Development tooling for language servers

options:
  -h, --help            show this help message and exit

commands:
  {capabilities,record}
    capabilities        dummy lsp server for recording a client's capabilities.
    record              record an LSP session.
```

```
usage: lsp-devtools record [-h] [-f FILE] [-r] [--format FORMAT] -- <SERVER_COMMAND>

This command runs the given language server command as a subprocess and records all messages sent between client and server.

options:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  save the log to a text file with the given filename

file options:
  these options only apply when --file is used

  -r, --raw             record all data, not just parsed messages
  --format FORMAT       format string to use with the log messages
```
