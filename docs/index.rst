LSP Devtools
============

The LSP Devtools project provides a number of tools for making the the
process of developing language servers easier.

Client Capability Index
-----------------------

.. important::

   This accuracy of this section entirely depends on the captured capabilities data that is `bundled <https://github.com/swyddfa/lsp-devtools/tree/develop/lib/pytest-lsp/pytest_lsp/clients>`__ with pytest-lsp.

   Pull requests for corrections and new data welcome!

.. toctree::
   :glob:
   :hidden:
   :caption: Client Capabilities

   capabilities/*

Inspired by `caniuse.com <https://caniuse.com>`__ this provides information on which clients support which features of the `LSP Specification <https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/>`__.

.. grid:: 2
   :gutter: 2

   .. grid-item-card:: General
      :columns: 12
      :link: /capabilities/general
      :link-type: doc
      :text-align: center

      General client capabilities.

   .. grid-item-card:: NotebookDocument
      :link: /capabilities/notebook-document
      :link-type: doc
      :text-align: center

      Capabilities for NotebookDocuments.

   .. grid-item-card:: TextDocument
      :link: /capabilities/text-document
      :link-type: doc
      :text-align: center

      Capabilities for text document methods like completion, code actions and more.

   .. grid-item-card:: Window
      :link: /capabilities/window
      :link-type: doc
      :text-align: center

      Work done progress, show document and message requests

   .. grid-item-card:: Workspace
      :link: /capabilities/workspace
      :link-type: doc
      :text-align: center

      File operations, workspace folders and configuration

lsp-devtools
------------

.. toctree::
   :hidden:
   :caption: lsp-devtools

   lsp-devtools/guide
   lsp-devtools/changelog


.. figure:: https://user-images.githubusercontent.com/2675694/273293510-e43fdc92-03dd-40c9-aaca-ddb5e526031a.png

The `lsp-devtools <https://pypi.org/project/lsp-devtools>`_ package provides a collection of CLI utilities that help inspect and visualise the interactions between a language client and a server.

See the :doc:`lsp-devtools/guide/getting-started` guide for details.

pytest-lsp
----------

.. toctree::
   :hidden:
   :caption: pytest-lsp

   pytest-lsp/guide
   pytest-lsp/howto
   pytest-lsp/reference
   pytest-lsp/changelog

`pytest-lsp <https://pypi.org/project/pytest-lsp>`_ is a pytest plugin for writing end-to-end tests for language servers.

.. literalinclude:: ./pytest-lsp/guide/window-log-message-output.txt
   :language: none

It works by running the language server in a subprocess and communicating with it over stdio, just like a real language client.
This also means ``pytest-lsp`` can be used to test language servers written in any language - not just Python.

``pytest-lsp`` relies on `pygls <https://github.com/openlawlibrary/pygls>`__ for its language server protocol implementation.

See the :doc:`pytest-lsp/guide/getting-started` guide for details on how to write your first test case.
