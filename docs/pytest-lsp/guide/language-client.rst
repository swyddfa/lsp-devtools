Language Client
===============

.. highlight:: none

The pytest-lsp :class:`~pytest_lsp.LanguageClient` supports the following LSP requests and notifications.

``window/logMessage``
---------------------

Any :lsp:`window/logMessage` notifications sent from the server will be accesible via the client's :attr:`~pytest_lsp.LanguageClient.log_messages` attribute.
This allows you to write test cases that check for the presence of particular log messages.

.. card:: test_server.py

   .. literalinclude:: ../../../lib/pytest-lsp/tests/examples/window-log-message/t_server.py
      :language: python
      :start-at: async def test_

.. card:: server.py

   .. literalinclude:: ../../../lib/pytest-lsp/tests/examples/window-log-message/server.py
      :language: python
      :start-at: @server.feature
      :end-at: return items

If a test case fails ``pytest-lsp`` will also include any captured log messages in the error report::

  ================================== test session starts ====================================
  platform linux -- Python 3.11.2, pytest-7.2.0, pluggy-1.0.0
  rootdir: /..., configfile: tox.ini
  plugins: typeguard-2.13.3, asyncio-0.20.2, lsp-0.2.1
  asyncio: mode=Mode.AUTO
  collected 1 item

  test_server.py F                                                                      [100%]

  ======================================== FAILURES =========================================
  ____________________________________ test_completions _____________________________________

  client = <pytest_lsp.client.LanguageClient object at 0x7f38f144a690>
     ...
  E       assert False

  test_server.py:35: AssertionError
  ---------------------------- Captured window/logMessages call -----------------------------
    LOG: Suggesting item 0
    LOG: Suggesting item 1
    LOG: Suggesting item 2
    LOG: Suggesting item 3
    LOG: Suggesting item 4
    LOG: Suggesting item 5
    LOG: Suggesting item 6
    LOG: Suggesting item 7
    LOG: Suggesting item 8
    LOG: Suggesting item 9
  ================================ short test summary info ==================================
  FAILED test_server.py::test_completions - assert False
  =================================== 1 failed in 1.02s =====================================
