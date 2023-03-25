Getting Started
===============

This guide will walk you through the process of writing your first test case using ``pytest-lsp``.

A Simple Language Server
------------------------

Before we can write any tests, we need a language server to test!
For the purposes of this example we'll write a simple language server in Python using the `pygls`_ library but note that ``pytest-lsp`` should work with language servers written in any language or framework.

The following server implements the ``textDocument/completion`` method

.. literalinclude:: ../../../lib/pytest-lsp/tests/examples/getting-started/server.py
   :language: python
   :end-at: ]

Copy and paste the above code into a file named ``server.py``.

A Simple Test Case
------------------

Now we can go ahead and test it.
Copy the following code and save it into a file named ``test_server.py``, in the same directory as the ``server.py`` file you created in the previous step.

.. literalinclude:: ../../../lib/pytest-lsp/tests/examples/getting-started/t_server.py
   :language: python
   :end-at: await lsp_client.shutdown()

This creates a `pytest fixture`_ named ``client``, it uses the given ``server_command`` to automatically launch the server in a background process and connect it to a ``LanguageClient`` instance.

The setup code (everything before the ``yield``) statement is executed before any tests run, calling ``initialize`` on the client to open the LSP session.

Once all test cases have been called, the code after the ``yield`` statement will be called to shutdown the server and close the session

With the framework in place, we can go ahead and define our first test case

.. literalinclude:: ../../../lib/pytest-lsp/tests/examples/getting-started/t_server.py
   :language: python
   :start-at: async def test_

All that's left is to run the test suite!

.. code-block:: none

   $ pytest
   ================================================ test session starts =================================================
   platform linux -- Python 3.11.2, pytest-7.2.0, pluggy-1.0.0
   rootdir: /var/home/user/Projects/lsp-devtools/lib/pytest-lsp, configfile: pyproject.toml
   plugins: typeguard-2.13.3, asyncio-0.20.2, lsp-0.2.1
   asyncio: mode=Mode.AUTO
   collected 1 item

   test_server.py E                                                                                               [100%]

   ======================================================= ERRORS =======================================================
   _________________________________________ ERROR at setup of test_completions _________________________________________

   lsp_client = <pytest_lsp.client.LanguageClient object at 0x7f9bd7e22050>

       @pytest_lsp.fixture(
           config=ClientServerConfig(server_command=[sys.executable, "server.py"]),
       )
       async def client(lsp_client: LanguageClient):
           # Setup
           params = InitializeParams(capabilities=ClientCapabilities())
   >       await lsp_client.initialize(params)

   test_server.py:18:
   _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
   ../../pytest_lsp/client.py:342: in initialize
       response = await self.initialize_request(params)
   _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

   self = <pytest_lsp.client.LanguageClient object at 0x7f9bd7e22050>
   params = InitializeParams(capabilities=ClientCapabilities(workspace=None, text_document=None, notebook_document=None, window=No..., root_path=None, root_uri=None, initialization_options=None, trace=None, work_done_token=None, workspace_folders=None)

       async def initialize_request(self, params: InitializeParams) -> lsprotocol.types.InitializeResult:
           """Make a ``initialize`` request.

           The initialize request is sent from the client to the server.

           It is sent once as the request after starting up the server. The
           requests parameter is of type {@link InitializeParams} the response
           if of type {@link InitializeResult} of a Thenable that resolves to
           such.
           """
   >       return await self.lsp.send_request_async("initialize", params)
   E       asyncio.exceptions.CancelledError: RuntimeError: Server exited with return code: 0
   E
   E       NoneType: None

   ../../pytest_lsp/gen.py:146: CancelledError
   ============================================== short test summary info ===============================================
   ERROR test_server.py::test_completions - asyncio.exceptions.CancelledError: RuntimeError: Server exited with return...
   ================================================== 1 error in 1.14s ==================================================

Ah, looks like we forgot to start the server.
Add the following to the bottom of ``server.py``.

.. code-block:: python

   if __name__ == "__main__":
       server.start_io()

Let's try again


.. code-block:: none

   $ pytest
   ================================================ test session starts =================================================
   platform linux -- Python 3.11.2, pytest-7.2.0, pluggy-1.0.0
   rootdir: /var/home/user/Projects/lsp-devtools/lib/pytest-lsp, configfile: pyproject.toml
   plugins: typeguard-2.13.3, asyncio-0.20.2, lsp-0.2.1
   asyncio: mode=Mode.AUTO
   collected 1 item

   test_server.py .                                                                                               [100%]

   ================================================= 1 passed in 0.96s ==================================================

Much better!


.. _pygls: https://github.com/openlawlibrary/pygls
.. _pytest fixture: https://docs.pytest.org/en/7.1.x/how-to/fixtures.html
