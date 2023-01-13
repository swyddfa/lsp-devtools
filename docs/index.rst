LSP Devtools
============

The LSP Devtools project provides a number of tools that aim to make the
process of developing language servers and clients easier.


pytest-lsp
----------

.. toctree::
   :maxdepth: 1
   :glob:
   :hidden:
   :caption: pytest-lsp

   pytest-lsp/*

End-to-end testing of language servers with pytest.

.. note::

   This plugin is in early development, it currently implements just enough to support the test suite of the
   `esbonio <https://github.com/swyddfa/esbonio>`__
   language server.

``pytest-lsp`` is a pytest plugin for writing end-to-end tests for language servers.

It works by running the language server in a subprocess and communicating with it over stdio, just like a real language client.
This also means ``pytest-lsp`` can be used to test language servers written in any language - not just Python.

``pytest-lsp`` relies on `pygls <https://github.com/openlawlibrary/pygls>`__ for its language server protocol implementation.

.. code-block:: python

   import sys
   import pytest
   import pytest_lsp
   from pytest_lsp import ClientServerConfig


   @pytest_lsp.fixture(
       scope='session',
       config=ClientServerConfig(
           server_command=[sys.executable, "-m", "esbonio"],
           root_uri="file:///path/to/test/project/root/"
       ),
   )
   async def client():
       pass


   @pytest.mark.asyncio
   async def test_completion(client):
       test_uri="file:///path/to/test/project/root/test_file.rst"
       result = await client.completion_request(test_uri, line=5, character=23)

       assert len(result.items) > 0
