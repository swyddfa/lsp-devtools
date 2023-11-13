## v0.2.1 - 2023-11-13


### Enhancements

- If the agent is unable to connect to a server app immediately, it will now retry indefinitely until it succeeds or the language server exits ([#77](https://github.com/swyddfa/lsp-devtools/issues/77))
- It is now possible to select completion items in the ``lsp-devtools client`` ([#108](https://github.com/swyddfa/lsp-devtools/issues/108))
- Commands like ``lsp-devtools record`` and ``lsp-devtools inspect`` will no longer exit/stop capturing messages after the first LSP session exits ([#110](https://github.com/swyddfa/lsp-devtools/issues/110))


## v0.2.0 - 2023-10-06

### Features

- **Experimental** Add proof of concept `lsp-devtools client` command that builds on textual's `TextArea` widget to offer an interactive language server client. ([#83](https://github.com/swyddfa/lsp-devtools/issues/83))

### Fixes

- The `lsp-devtools agent` command no longer fails to exit once an LSP session closes. ([#17](https://github.com/swyddfa/lsp-devtools/issues/17))
- `lsp-devtools record` no longer emits a `ResourceWarning` ([#28](https://github.com/swyddfa/lsp-devtools/issues/28))
- As a consequence of the new architecture, commands like `lsp-devtools record` no longer miss the start of an LSP session ([#29](https://github.com/swyddfa/lsp-devtools/issues/29))
- `lsp-devtools agent` no longer emits `Unable to send data, no available transport!` messages ([#38](https://github.com/swyddfa/lsp-devtools/issues/38))

### Misc

- The `lsp-devtools agent` now uses a TCP connection, which should make distribution easier ([#37](https://github.com/swyddfa/lsp-devtools/issues/37))

- Drop Python 3.7 support ([#77](https://github.com/swyddfa/lsp-devtools/issues/77))

- The `lsp-devtools capabilities` command has been removed in favour of `lsp-devtools record`

  The `lsp-devtools tui` command has been renamed to `lsp-devtools inspect` ([#83](https://github.com/swyddfa/lsp-devtools/issues/83))

## v0.1.1 - 2023-01-14

### Fixes

- Fix PyPi packaging ([#33](https://github.com/alcarney/lsp-devtools/issues/33))

## v0.1.0 - 2023-01-10

### Features

- Updated `record` command.

  It is now capable of live streaming messages sent between a client and server to stdout, plain text files or a SQLite database.

  It also offers a number of filters for selecting the messages you wish to record, as well as a (WIP!) format string syntax for controlling how messages are formatted. ([#26](https://github.com/alcarney/lsp-devtools/issues/26))

- Add `tui` command.

  A proof of concept devtools TUI implemented in textual, that live updates with the LSP messages sent between client and server!

  Requires the server be wrapped in an `agent`. ([#27](https://github.com/alcarney/lsp-devtools/issues/27))

### Misc

- Migrated to `v1.0` ([#26](https://github.com/alcarney/lsp-devtools/issues/26))

## v0.0.3 - 2022-07-17

### Misc

- Remove upper bound on required `pygls` version ([#14](https://github.com/alcarney/lsp-devtools/issues/14))

## v0.0.2 - 2022-05-06

### Fixes

- Fix `mypy` errors. ([#7](https://github.com/alcarney/lsp-devtools/issues/7))

## v0.0.1 - 2022-04-29

### Misc

- Initial release ([#6](https://github.com/alcarney/lsp-devtools/issues/6))
