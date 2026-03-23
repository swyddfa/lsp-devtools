## v0.4.0 - 2026-03-23

### Features

- The server command used with the `lsp-devtools client` command can now be configured at runtime.

  Server process lifecycle information and errors are now also logged to the `Server` panel. ([#234](https://github.com/swyddfa/lsp-devtools/issues/234))

### Fixes

- Fix issue where `lsp-devtools inspect` would not exit cleanly ([#229](https://github.com/swyddfa/lsp-devtools/issues/229))
- Fix crash caused by trying to dismiss the message filter dialog twice. ([#231](https://github.com/swyddfa/lsp-devtools/issues/231))

### Misc

- Bump textual to `>=8.1.0` ([#233](https://github.com/swyddfa/lsp-devtools/issues/233))


## v0.3.0 - 2026-03-02

### Features

- Add Windows support ([#125](https://github.com/swyddfa/lsp-devtools/issues/125))

### Enhancements

- The `lsp-devtools record` command now accepts multiple format strings (e.g. `-f {message.method} -f {message.result}`). They will be tried in the order given, with messages using the format first string that applies cleanly. ([#122](https://github.com/swyddfa/lsp-devtools/issues/122))
- The `lsp-devtools record` command now accepts an `--keep-unformatted` option, which will preserve messages in the log that could not be formatted using one of the provided format strings. They will instead be formatted using the default format string for the command. ([#123](https://github.com/swyddfa/lsp-devtools/issues/123))
- The format string syntax has been changed to be more inline with how regular Python format strings work e.g.

  - *before* `{.params|json}` *now* `{message.params:json}`

  There is now an option that controls if the `lsp-devtools record` command should exit (`--on-disconnect exit`) when it loses the connection to the agent, or if it should continue running (`--on-disconnect continue`), which is still the default behaviour

  ([#211](https://github.com/swyddfa/lsp-devtools/issues/211))

### Misc

- Update pygls to v2
  Update textual to v6.x

  Add support for Python 3.13 & 3.14.
  Drop support for Python 3.9 ([#203](https://github.com/swyddfa/lsp-devtools/issues/203))


## v0.2.4 - 2024-11-23

### Fixes

- The `lsp-devtools agent` should now suppress `asyncio.CancelledError` exceptions allowing the agent to process to terminate gracefully ([#191](https://github.com/swyddfa/lsp-devtools/issues/191))

### Misc

- Drop Python 3.8 support ([#190](https://github.com/swyddfa/lsp-devtools/issues/190))
- Migrate to pygls `v2.0a2` ([#192](https://github.com/swyddfa/lsp-devtools/issues/192))


## v0.2.3 - 2024-05-22


### Enhancements

- The `lsp-devtools agent` now forwards the server's `stderr` channel ([#165](https://github.com/swyddfa/lsp-devtools/issues/165))

### Fixes

- All `lsp-devtools` commands should no longer crash when encountering messages containing unicode characters ([#157](https://github.com/swyddfa/lsp-devtools/issues/157))
- Commands like `lsp-devtools record` should now continue to function after encountering an error ([#158](https://github.com/swyddfa/lsp-devtools/issues/158))


## v0.2.2 - 2024-01-29


### Enhancements

- Added formatters `json` and `json-compact` that can be used within format strings. ([#130](https://github.com/swyddfa/lsp-devtools/issues/130))
- When not printing messages to stdout, the `lsp-devtools record` command now displays a nice visualisation of the traffic between client and server - so that you can see that it's doing something ([#134](https://github.com/swyddfa/lsp-devtools/issues/134))

### Fixes

- The `lsp-devtools record` command will now produce valid JSON when using the `--to-file` option without an explicitly provided format string. ([#130](https://github.com/swyddfa/lsp-devtools/issues/130))
- The `lsp-devtools agent` now watches for the when the server process exits and closes itself down also. ([#132](https://github.com/swyddfa/lsp-devtools/issues/132))
- Commands like `lsp-devtools record` should now exit cleanly when hitting `Ctrl-C` ([#133](https://github.com/swyddfa/lsp-devtools/issues/133))


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
