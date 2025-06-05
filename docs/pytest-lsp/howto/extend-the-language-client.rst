.. _howto-extend-client:

How To Extend the Default ``LanguageClient``
============================================

There will likely come a point where you will want to modify some aspect of the default language client's behaviour - or replace it entirely with your own.
This guide will walk through the various options for adjusting the client and its behaviour

- :ref:`howto-extend-client-new-methods`
- :ref:`howto-extend-client-replace-methods`
- :ref:`howto-extend-client-custom-client`

.. _howto-extend-client-new-methods:

Adding new methods
------------------

If you need to add support to the client for an LSP method it does not yet support, this can be done inside your setup fixture.

.. literalinclude:: ../../../lib/pytest-lsp/tests/examples/add-client-method/t_server.py
   :language: python
   :start-at: @pytest_lsp
   :end-at: await lsp_client.shutdown_session

.. _howto-extend-client-replace-methods:

Replacing methods
-----------------

Replacing an existing method's implementation will require you to setup your own client factory function.

#. First write your custom method implementation.
   As an example, we'll fail the test if the server tries to send diagnostics via the :lsp:`textDocument/publishDiagnostics` notification.

   .. literalinclude:: ../../../lib/pytest-lsp/tests/examples/replace-client-method/t_server.py
      :language: python
      :start-at: def disallow_publish_diagnostics
      :end-at: raise RuntimeError

#. Write your own client factory function, you will need to construct your own mapping from lsp method names to the corresponding handler functions.

   The :data:`~pytest_lsp.client.DEFAULT_CLIENT_FEATURES` dictionary will include all of the built in handlers.

   Pass your mapping and client instance to the :func:`~pytest_lsp.client.register_lsp_features` function to register them.

   .. literalinclude:: ../../../lib/pytest-lsp/tests/examples/replace-client-method/t_server.py
      :language: python
      :start-at: from pygls.protocol import default_converter
      :end-at: return client

#. Finally, use your custom client factory function with the :class:`~pytest_lsp.plugin.ClientServerConfig` you pass to your fixture function.

   .. literalinclude:: ../../../lib/pytest-lsp/tests/examples/replace-client-method/t_server.py
      :language: python
      :start-at: @pytest_lsp.fixture
      :end-at: await lsp_client.shutdown_session

.. _howto-extend-client-custom-client:

Using a Custom Client Class
----------------------------

Using your own custom ``LanguageClient`` class is very similar to :ref:`howto-extend-client-replace-methods`, just create an instance of your language client in your factory function.

.. important::

   Your custom language client **must** inherit from the default ``LanguageCient`` class

.. code-block:: python

   from pygls.protocol import default_converter
   from pytest_lsp import LanguageClient
   from pytest_lsp.client import DEFAULT_CLIENT_FEATURES, register_lsp_features

   class MyLanguageClient(LanguageClient):
       pass

   def my_make_test_lsp_client() -> LanguageClient:
       """Return a custom language client"""
       client = MyLanguageClient(
           converter_factory=default_converter,
       )
       register_lsp_features(client, DEFAULT_CLIENT_FEATURES)
       return client
