## v0.4.3 - 2024-08-28

### Fixes

- The client now waits for the server process to gracefully exit by @OhioDschungel6 ([#173](https://github.com/swyddfa/lsp-devtools/issues/173))


## v0.4.2 - 2024-05-22


### Client Capabilities

- Add client capabilities for Neovim v0.10.0 ([#164](https://github.com/swyddfa/lsp-devtools/issues/164))

### Misc

- Start testing against pytest v8 ([#145](https://github.com/swyddfa/lsp-devtools/issues/145))


## v0.4.1 - 2024-02-07


### Enhancements

- When a test fails `pytest-lsp` will now show the server's `stderr` output (if any) ([#143](https://github.com/swyddfa/lsp-devtools/issues/143))

### Client Capabilities

- Add client capabilities for Emacs v29.1 ([#142](https://github.com/swyddfa/lsp-devtools/issues/142))

### Fixes

- `LspSpecificationWarnings` will no longer be incorrectly emitted when a client does indeed support `window/workDoneProgress/create` requests ([#119](https://github.com/swyddfa/lsp-devtools/issues/119))

### Misc

- Bump minimum version of `pytest-asyncio` to `0.23.0` ([#126](https://github.com/swyddfa/lsp-devtools/issues/126))


## v0.4.0 - 2023-11-13


### Features

- The test ``LanguageClient`` now supports ``workspace/configuration`` requests ([#90](https://github.com/swyddfa/lsp-devtools/issues/90))
- pytest-lsp's ``LanguageClient`` is now able to handle ``window/workDoneProgress/create`` requests. ([#91](https://github.com/swyddfa/lsp-devtools/issues/91))
- ``pytest-lsp`` is now able to integrate with ``lsp-devtools``, run ``pytest`` with the ``--lsp-devtools`` flag to enable the integration. ([#97](https://github.com/swyddfa/lsp-devtools/issues/97))

### Enhancements

- It is now possible to select a specific version of a client when using the ``client_capabilities()`` function.
  e.g. ``client-name@latest``, ``client-name@v2`` or ``client-name@2.1.3``. ``pytest-lsp`` will choose the latest available version of the client that satisfies the given constraint. ([#101](https://github.com/swyddfa/lsp-devtools/issues/101))

### Client Capabilities

- Add client capabilities for Neovim versions ``v0.7.0`` and ``v0.8.0`` ([#89](https://github.com/swyddfa/lsp-devtools/issues/89))
- Add client capabilities for Neovim ``v0.9.1`` ([#100](https://github.com/swyddfa/lsp-devtools/issues/100))


## v0.3.1 - 2023-10-06

This release includes some minor breaking changes if you were using the lower-level APIs e.g `make_client_server`.

See [this commit](https://github.com/swyddfa/esbonio/commit/8565add660ad015c989cd3c4a251dede92525997) for a sample migration

### Enhancements

- pytest-lsp's `LanguageClient` is now based on the one provided by `pygls`.
  The main benefit is that the server connection is now based on an `asyncio.subprocess.Process` removing the need for pytest-lsp to constantly check to see if the server is still running. ([#61](https://github.com/swyddfa/lsp-devtools/issues/61))
- Fixtures created with the `@pytest_lsp.fixture` decorator can now request additional pytest fixtures ([#71](https://github.com/swyddfa/lsp-devtools/issues/71))
- It is now possible to set the environment variables that the server under test is launched with. ([#72](https://github.com/swyddfa/lsp-devtools/issues/72))
- It is now possible to test any JSON-RPC based server with `pytest-lsp`.
  Note however, this support will only ever extend to managing the client-server connection. ([#73](https://github.com/swyddfa/lsp-devtools/issues/73))

### Misc

- `make_test_client` has been renamed to `make_test_lsp_client` ([#73](https://github.com/swyddfa/lsp-devtools/issues/73))
- Drop support for Python 3.7, add support for Python 3.12 ([#75](https://github.com/swyddfa/lsp-devtools/issues/75))

## v0.3.0 - 2023-05-19

### Features

- `@pytest_lsp.fixture` now supports the `yield` statement, allowing the `client` fixture definition to be responsible for initialising and shutting down the LSP session granting the test author full control over the contents of the `initialize` request.

  This is a breaking change, see the documentation for details and [this PR](https://github.com/swyddfa/esbonio/pull/571) for an example migration. ([#47](https://github.com/swyddfa/lsp-devtools/issues/47))

- If a client's capabilities has been set, pytest-lsp will automatically check the server's response to see if it is compatible with the capabilities the client provided.

  If an issue is detected, pytest-lsp will emit an `LspSpecificationWarning`

  **Note:** This relies on a dedicated `check_xxx` function being written for each request so only a subset of the LSP spec is currently supported. ([#57](https://github.com/swyddfa/lsp-devtools/issues/57))

### Docs

- Add getting started guide ([#47](https://github.com/swyddfa/lsp-devtools/issues/47))
- Add note on redefining the `event_loop` fixture to match the client fixture's scope ([#49](https://github.com/swyddfa/lsp-devtools/issues/49))
- Add documentation on the built in features of the test LSP client ([#50](https://github.com/swyddfa/lsp-devtools/issues/50))
- Add example on using parameterised fixtures to test with multiple clients ([#51](https://github.com/swyddfa/lsp-devtools/issues/51))

### Misc

- The client-server connection is now managed by a single asyncio event loop, rather than spinning up multiple threads, resulting in a much simpler architecture. ([#44](https://github.com/swyddfa/lsp-devtools/issues/44))

### Removed

- Helper methods like `completion_request` and `notify_did_open` have been removed.
  The equivalent methods provided by the LSP specification like `text_document_completion_async` and `text_document_did_open` should be used directly.

  See [this PR](https://github.com/swyddfa/esbonio/pull/571) for an example migration. ([#56](https://github.com/swyddfa/lsp-devtools/issues/56))

## v0.2.1 - 2023-01-14

### Fixes

- Ensure that the test client returns a `ShowDocumentResult` for `window/showDocument` requests. ([#34](https://github.com/alcarney/lsp-devtools/issues/34))

## v0.2.0 - 2023-01-10

### Features

- The `LanguageClient` now exposes methods covering the full LSP spec thanks to autogenerating its client from type definitions provided by `lsprotocol` ([#25](https://github.com/alcarney/lsp-devtools/issues/25))

### Misc

- Support for Python 3.6 has been dropped.

  Support for Python 3.11 has been added.

  Upgraded to pygls 1.0. ([#25](https://github.com/alcarney/lsp-devtools/issues/25))

## v0.1.3 - 2022-10-15

### Fixes

- - Check that server provided for testing doesn't crash within the first 0.1 seconds
  - Return `INITIALIZE` response from `ClientServer.start()`. This allows tests to assert against the server's `INITIALIZE` response without resending the `INITIALIZE` request in the actual test. ([#22](https://github.com/alcarney/lsp-devtools/issues/22))

## v0.1.2 - 2022-07-18

### Enhancements

- Add helpers for `textDocument/implementation` requests ([#15](https://github.com/alcarney/lsp-devtools/issues/15))

## v0.1.1 - 2022-07-17

### Misc

- Remove upper bound on required `pygls` version ([#14](https://github.com/alcarney/lsp-devtools/issues/14))

## v0.1.0 - 2022-07-02

### Features

- Any `window/logMessage` messages emitted by a server under test are now captured and reported alongside any test failures ([#5](https://github.com/alcarney/lsp-devtools/issues/5))

### Enhancements

- For currently implemented lsp request helpers, the test client now supports all valid return types. ([#11](https://github.com/alcarney/lsp-devtools/issues/11))

### Fixes

- The test client now correctly handles `null` responses. ([#9](https://github.com/alcarney/lsp-devtools/issues/9))

## v0.0.7 - 2022-05-26

### Enhancements

- Add helpers for `textDocument/hover` requests. ([#8](https://github.com/alcarney/lsp-devtools/issues/8))

## v0.0.6 - 2022-04-18

### Enhancements

- Added helpers for `textDocument/documentLink` requests. ([#4](https://github.com/alcarney/lsp-devtools/issues/4))

## v0.0.5 - 2022-04-02

### Fixes

- The plugin should now work on Python v3.6+ ([#1](https://github.com/alcarney/lsp-devtools/issues/1))

## v0.0.3 - 2022-03-28

### Removed

- Removed `event_loop` fixture

## v0.0.3 - 2022-03-28

### Fixes

- Fixture creation on Python 3.6 should now work

## v0.0.2 - 2022-03-28

### Fixes

- Ensure the `py.typed` file is packaged.
- The `importlib_resources` import on Python 3.6 should now work

## v0.0.1 - 2022-03-28

Initial Release
