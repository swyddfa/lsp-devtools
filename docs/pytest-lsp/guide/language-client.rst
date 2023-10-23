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
      :start-at: @pytest.mark.asyncio


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
      :start-at: @pytest.mark.asyncio

.. card:: server.py

   .. literalinclude:: ../../../lib/pytest-lsp/tests/examples/window-log-message/server.py
      :language: python
      :start-at: @server.feature
      :end-at: return items

If a test case fails ``pytest-lsp`` will also include any captured log messages in the error report

.. literalinclude:: ./window-log-message-output.txt

``window/showDocument``
-----------------------

Similar to ``window/logMessage`` above, the client records any :lsp:`window/showDocument` notifications and are accessible via its :attr:`~pytest_lsp.LanguageClient.shown_documents` attribute.

.. card:: test_server.py

   .. literalinclude:: ../../../lib/pytest-lsp/tests/examples/window-show-document/t_server.py
      :language: python
      :start-at: @pytest.mark.asyncio

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
      :start-at: @pytest.mark.asyncio

.. card:: server.py

   .. literalinclude:: ../../../lib/pytest-lsp/tests/examples/window-show-message/server.py
      :language: python
      :start-at: @server.feature
      :end-at: return items

``workspace/configuration``
---------------------------

The client can respond to :lsp:`workspace/configuration` requests.

The client supports settings different configuration values for different ``scope_uris`` as well as getting/setting specific configuration ``sections``.
However, to keep the implementation simple the client **will not** fallback to more general configuration scopes if it cannot find a value in the requested scope.

See the documentation on :meth:`~pytest_lsp.LanguageClient.set_configuration` and :meth:`~pytest_lsp.LanguageClient.get_configuration` for details

.. card:: test_server.py

   .. literalinclude:: ../../../lib/pytest-lsp/tests/examples/workspace-configuration/t_server.py
      :language: python
      :start-at: @pytest.mark.asyncio

.. card:: server.py

   .. literalinclude:: ../../../lib/pytest-lsp/tests/examples/workspace-configuration/server.py
      :language: python
      :start-at: @server.command
      :end-at: return a + c
