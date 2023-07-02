LSP Devtools
============

The LSP Devtools project provides a number of tools that aim to make the
process of developing language servers and clients easier.

lsp-devtools
------------

.. toctree::
   :hidden:
   :caption: lsp-devtools

   lsp-devtools/guide
   lsp-devtools/changelog


The `lsp-devtools <https://pypi.org/project/lsp-devtools>`_ package provides a collection of CLI utilities that help inspect and visualise the interactions between a language client and a server.

See the :doc:`lsp-devtools/guide/getting-started` guide for details.

pytest-lsp
----------

.. toctree::
   :hidden:
   :caption: pytest-lsp

   pytest-lsp/guide
   pytest-lsp/reference
   pytest-lsp/changelog

`pytest-lsp <https://pypi.org/project/pytest-lsp>`_ is a pytest plugin for writing end-to-end tests for language servers.

.. literalinclude:: ./pytest-lsp/guide/window-log-message-output.txt
   :language: none

It works by running the language server in a subprocess and communicating with it over stdio, just like a real language client.
This also means ``pytest-lsp`` can be used to test language servers written in any language - not just Python.

``pytest-lsp`` relies on `pygls <https://github.com/openlawlibrary/pygls>`__ for its language server protocol implementation.

See the :doc:`pytest-lsp/guide/getting-started` guide for details on how to write your first test case.
