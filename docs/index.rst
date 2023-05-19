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

   pytest-lsp/guide
   pytest-lsp/reference
   pytest-lsp/changelog



``pytest-lsp`` is a pytest plugin for writing end-to-end tests for language servers.

It works by running the language server in a subprocess and communicating with it over stdio, just like a real language client.
This also means ``pytest-lsp`` can be used to test language servers written in any language - not just Python.

``pytest-lsp`` relies on `pygls <https://github.com/openlawlibrary/pygls>`__ for its language server protocol implementation.

See the :doc:`pytest-lsp/guide/getting-started` guide for details on how to write your first test case.
