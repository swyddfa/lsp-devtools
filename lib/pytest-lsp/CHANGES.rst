v0.1.0 - 2022-07-02
-------------------

Features
^^^^^^^^

- Any ``window/logMessage`` messages emitted by a server under test are now captured and reported alongside any test failures (`#5 <https://github.com/alcarney/lsp-devtools/issues/5>`_)


Enhancements
^^^^^^^^^^^^

- For currently implemented lsp request helpers, the test client now supports all valid return types. (`#11 <https://github.com/alcarney/lsp-devtools/issues/11>`_)


Fixes
^^^^^

- The test client now correctly handles ``null`` responses. (`#9 <https://github.com/alcarney/lsp-devtools/issues/9>`_)


v0.0.7 - 2022-05-26
-------------------

Enhancements
^^^^^^^^^^^^

- Add helpers for ``textDocument/hover`` requests. (`#8 <https://github.com/alcarney/lsp-devtools/issues/8>`_)


v0.0.6 - 2022-04-18
-------------------

Enhancements
^^^^^^^^^^^^

- Added helpers for ``textDocument/documentLink`` requests. (`#4 <https://github.com/alcarney/lsp-devtools/issues/4>`_)


v0.0.5 - 2022-04-02
-------------------

Fixes
^^^^^

- The plugin should now work on Python v3.6+ (`#1 <https://github.com/alcarney/lsp-devtools/issues/1>`_)


v0.0.3 - 2022-03-28
-------------------

Removed
^^^^^^^

- Removed ``event_loop`` fixture

v0.0.3 - 2022-03-28
-------------------

Fixes
^^^^^

- Fixture creation on Python 3.6 should now work

v0.0.2 - 2022-03-28
--------------------

Fixes
^^^^^

- Ensure the ``py.typed`` file is packaged.
- The ``importlib_resources`` import on Python 3.6 should now work

v0.0.1 - 2022-03-28
--------------------

Initial Release