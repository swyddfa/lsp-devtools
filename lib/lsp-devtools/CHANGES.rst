v0.1.1 - 2023-01-14
-------------------

Fixes
^^^^^

- Fix PyPi packaging (`#33 <https://github.com/alcarney/lsp-devtools/issues/33>`_)


v0.1.0 - 2023-01-10
-------------------

Features
^^^^^^^^

- Updated ``record`` command.

  It is now capable of live streaming messages sent between a client and server to stdout, plain text files or a SQLite database.

  It also offers a number of filters for selecting the messages you wish to record, as well as a (WIP!) format string syntax for controlling how messages are formatted. (`#26 <https://github.com/alcarney/lsp-devtools/issues/26>`_)
- Add ``tui``command.

  A proof of concept devtools TUI implemented in textual, that live updates with the LSP messages sent between client and server!

  Requires the server be wrapped in an ``agent``. (`#27 <https://github.com/alcarney/lsp-devtools/issues/27>`_)


Misc
^^^^

- Migrated to ``v1.0`` (`#26 <https://github.com/alcarney/lsp-devtools/issues/26>`_)


v0.0.3 - 2022-07-17
-------------------

Misc
^^^^

- Remove upper bound on required ``pygls`` version (`#14 <https://github.com/alcarney/lsp-devtools/issues/14>`_)


v0.0.2 - 2022-05-06
-------------------

Fixes
^^^^^

- Fix ``mypy`` errors. (`#7 <https://github.com/alcarney/lsp-devtools/issues/7>`_)


v0.0.1 - 2022-04-29
-------------------

Misc
^^^^

- Initial release (`#6 <https://github.com/alcarney/lsp-devtools/issues/6>`_)
