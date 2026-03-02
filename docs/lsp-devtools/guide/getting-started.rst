Getting Started
===============

.. highlight:: none

This guide will introduce you to the tools available in the ``lsp-devtools`` suite of tools.
It's recommended that you install ``lsp-devtools`` into a standalone environment managed through tools like `pipx <https://pypi.org/project/pipx/>`__ or `uv <https://docs.astral.sh/uv/>`__

.. tab-set::

  .. tab-item:: pipx

     To install using ``pipx`` ::

        pipx install lsp-devtools

  .. tab-item:: uv

     To install using ``uv`` ::

        uv tool install lsp-devtools



The LSP Agent
-------------

In order to use most of the tools in ``lsp-devtools`` you need to wrap your language server with the LSP Agent.
The agent is a simple program that sits inbetween a language client and the server as shown in the diagram below.

.. figure:: /images/lsp-devtools-architecture.svg

   ``lsp-devtools`` architecture

The agent acts as a messenger, forwarding messages from the LSP client to the LSP server and vice versa.
It also sends a copy of each message over a local TCP connection to some "Server" application, typically another ``lsp-devtools`` command like ``lsp-devtool record`` or ``lsp-devtools inspect``.

In general, using ``lsp-devtools`` can be broken down into a 3 steps:

#. Configure your language client to launch your language server via the agent, rather than launching it directly.

#. Start the server application e.g. ``lsp-devtools record`` or ``lsp-devtools inspect``

#. Start your language client.

.. _lsp-devtools-configure-client:

Configuring your client
^^^^^^^^^^^^^^^^^^^^^^^

In order to wrap your language server with the LSP Agent, you need to be able to modify the command your language client uses to start your language server to the following::

  lsp-devtools agent -- <server-cmd>

The ``agent`` command will interpret anything given after the double dashes (``--``) to be the command used to invoke your language server.
By default, the agent will attempt to connect to a server application on ``localhost:8765`` but this can be changed using the ``--host <host>`` and ``--port <port>`` arguments::

  lsp-devtools agent --host 127.0.0.1 --port 1234 -- <server-cmd>

.. tip::

   Since the agent only requires your server's start command, you can use ``lsp-devtools`` with language servers written in any language.


As an example, let's configure
`neovim <https://github.com/neovim/neovim/>`__
to launch the
`esbonio <https://github.com/swyddfa/esbonio/>`__
language server directly, using the built-in language client and configuration syntax available in ``nvim v0.11`` onwards.

.. code-block:: lua

   vim.lsp.config.esbonio = {
     cmd = { 'esbonio' },
     root_markers = { 'conf.py' },
     filetypes = { 'rst' },
     settings = {
       esbonio = {
         logging = {
           level = 'debug'
         },
       },
     },
   }
   vim.lsp.enable({ 'esbonio' })

To update this to launch the ``esbonio`` via the ``lsp-devtools agent``, we need only modify the ``cmd`` field

.. code-block:: diff

     vim.lsp.config.esbonio = {
   -   cmd = { "esbonio" },
   +   cmd = { "lsp-devtools", "agent", "--", "esbonio" },
       ...
     }

Server Applications
-------------------

Once you have your client configured, you need to start the application the agent is going to try to connect to.
Currently ``lsp-devtools`` provides the following applications

``lsp-devtools record`` - see :doc:`recording sessions </lsp-devtools/guide/record-command>` for details
   As the name suggests, this command supports recording all (or a subset of) messages in a LSP session to a text file or SQLite database.
   It also supports printing these messages direct to the console.

   .. figure:: /images/record-example.svg

``lsp-devtools inspect`` -  see :doc:`inspecting sessions </lsp-devtools/guide/inspect-command>` for details
   An terminal application with the goal of making it easy to interactively visualise and explore the traffic sent between an LSP client ans server, inspired by the dev tools found in a web browser.

   Powered by `textual <https://pypi.org/project/textual>`__.

   .. figure:: /images/inspector-screenshot.svg
