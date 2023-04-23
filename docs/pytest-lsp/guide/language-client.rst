Language Client
===============

.. highlight:: none

The pytest-lsp :class:`~pytest_lsp.LanguageClient` supports the following LSP requests and notifications.

``textDocument/publishDiagnostics``
-----------------------------------

The client maintains a record of any :attr:`~pytest_lsp.LanguageClient.diagnostics` published by the server in a dictionary indexed by a text document's uri.

.. card:: test_server.py

   .. literalinclude:: ../../../lib/pytest-lsp/tests/examples/diagnostics/t_server.py
      :language: python
      :start-at: async def test_


.. note::

   While the client has the (rather useful!) ability to :func:`~pytest_lsp.LanguageClient.wait_for_notification` messages from the server, this is not something covered by the `LSP Specification`_.

.. _LSP Specification: https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/

.. card:: server.py

   .. literalinclude:: ../../../lib/pytest-lsp/tests/examples/diagnostics/server.py
      :language: python
      :start-at: @server.feature
      :end-before: if __name__ == "__main__"


``window/logMessage``
---------------------

Any :lsp:`window/logMessage` notifications sent from the server will be accessible via the client's :attr:`~pytest_lsp.LanguageClient.log_messages` attribute.

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

``window/showDocument``
-----------------------

Similar to ``window/logMessage`` above, the client records any :lsp:`window/showDocument` notifications and are accessible via its :attr:`~pytest_lsp.LanguageClient.shown_documents` attribute.

.. card:: test_server.py

   .. literalinclude:: ../../../lib/pytest-lsp/tests/examples/window-show-document/t_server.py
      :language: python
      :start-at: async def test_

.. card:: server.py

   .. literalinclude:: ../../../lib/pytest-lsp/tests/examples/window-show-document/server.py
      :language: python
      :start-at: @server.feature
      :end-at: return items


``window/showMessage``
----------------------

Similar to ``window/logMessage`` above, the client records any :lsp:`window/showMessage` notifications and are accessible via its :attr:`~pytest_lsp.LanguageClient.messages` attribute.

.. card:: test_server.py

   .. literalinclude:: ../../../lib/pytest-lsp/tests/examples/window-show-message/t_server.py
      :language: python
      :start-at: async def test_

.. card:: server.py

   .. literalinclude:: ../../../lib/pytest-lsp/tests/examples/window-show-message/server.py
      :language: python
      :start-at: @server.feature
      :end-at: return items
