How To Test Generic JSON-RPC Servers
====================================

While ``pytest-lsp`` is primarily focused on writing tests for LSP servers it is possible to reuse some of the machinery to test other JSON-RPC servers.

A Simple JSON-RPC Server
------------------------

As an example we'll reuse some of the `pygls`_ internals to write a simple JSON-RPC server that implements the following protocol.

- client to server request ``math/add``, returns the sum of two numbers ``a`` and ``b``
- client to server request ``math/sub``, returns the difference of two numbers ``a`` and ``b``
- client to server notification ``server/exit`` that instructs the server to exit
- server to client notification ``log/message``, allows the server to send debug messages to the client.

.. note::

   The details of the implementation below don't really matter as we just need *something* to help us illustrate how to use ``pytest-lsp`` in this way.

   Remember you can write your servers in whatever language/framework you prefer!

.. literalinclude:: ../../../lib/pytest-lsp/tests/examples/generic-rpc/server.py
   :language: python

Constructing a Client
---------------------

While ``pytest-lsp`` can manage the connection between client and server, it needs to be given a client that understands the protocol that the server implements.
This is done with a factory function

.. literalinclude:: ../../../lib/pytest-lsp/tests/examples/generic-rpc/t_server.py
   :language: python
   :start-at: def client_factory():
   :end-at: return client

The Client Fixture
------------------

Once you have your factory function defined you can pass it to the :class:`~pytest_lsp.ClientServerConfig` when defining your client fixture

.. literalinclude:: ../../../lib/pytest-lsp/tests/examples/generic-rpc/t_server.py
   :language: python
   :start-at: @pytest_lsp.fixture(
   :end-at: rpc_client.protocol.notify

Writing Test Cases
------------------

With the client fixuture defined, test cases are written almost identically as they would be for your LSP servers.
The only difference is that the generic :meth:`~pygls:pygls.protocol.JsonRPCProtocol.send_request_async` and :meth:`~pygls:pygls.protocol.JsonRPCProtocol.notify` methods are used to communicate with the server.

.. literalinclude:: ../../../lib/pytest-lsp/tests/examples/generic-rpc/t_server.py
   :language: python
   :start-at: @pytest.mark.asyncio

However, it is also possible to extend the base :class:`~pygls:pygls.client.JsonRPCClient` to provide a higher level interface to your server.
See the `SubprocessSphinxClient`_ from the `esbonio`_ project for such an example.

.. _esbonio: https://github.com/swyddfa/esbonio
.. _pygls: https://github.com/openlawlibrary/pygls
.. _SubprocessSphinxClient: https://github.com/swyddfa/esbonio/blob/develop/lib/esbonio/esbonio/server/features/sphinx_manager/client_subprocess.py
