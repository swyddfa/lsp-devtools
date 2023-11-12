How To Integrate ``pytest-lsp`` with ``lsp-devtools``
=====================================================

``pytest-lsp`` is able to forward LSP traffic to utilities like :doc:`lsp-devtools record </lsp-devtools/guide/record-command>` and :doc:`lsp-devtools inspect </lsp-devtools/guide/inspect-command>`

.. important::

   ``pytest-lsp`` does not depend on ``lsp-devtools`` directly and instead assumes that the ``lsp-devtools`` command is available on your ``$PATH``.
   It's recommended to install ``lsp-devtools`` via `pipx <https://pypa.github.io/pipx/>`__::

     $ pipx install lsp-devtools

To enable the integration pass the ``--lsp-devtools`` flag to ``pytest``::

  $ pytest --lsp-devtools

This will make ``pytest-lsp`` send the captured traffic to an ``lsp-devtools`` command listening on ``localhost:8765`` by default.

To change the default host and/or port number you can pass it to the ``--lsp-devtools`` cli option::

  $ pytest --lsp-devtools 1234            # change port number
  $ pytest --lsp-devtools 127.0.01:1234   # change host and port
