Getting Started
===============

.. highlight:: none

This guide will introduce you to the tools available in the ``lsp-devtools`` package.
If you have not done so already, you can install it using ``pipx`` ::

  pipx install lsp-devtools

.. admonition:: Did you say pipx?

   `pipx <https://pypi.org/project/pipx/>`_ is a tool that automates the process of installing Python packages into their own isolated Python environments - useful for standalone applications like ``lsp-devtools``

The LSP Agent
-------------

In order to use most of the tools in ``lsp-devtools`` you need to wrap your language server with the LSP Agent.
The agent is a simple program that sits inbetween a language client and the server as shown in the diagram below.

.. figure:: /images/lsp-devtools-architecture.svg

   ``lsp-devtools`` architecture

The agent acts as a messenger, forwarding messages from the client to the server and vice versa.
However, it sends an additional copy of each message over a local TCP connection to some "Server" application - typically another ``lsp-devtools`` command like ``record`` or ``tui``.

In general, using ``lsp-devtools`` can be broken down into a 3 step process.

#. Configure your language client to launch your language server via the agent, rather than launching it directly.

#. Start the server application e.g. ``lsp-devtools record`` or ``lsp-devtools tui``

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

   Since the agent only requires your server's start command, you can use ``lsp-devtools`` with a server written in any language.


As an example, let's configure Neovim to launch the ``esbonio`` language server via the agent.
Using `nvim-lspconfig <https://github.com/neovim/nvim-lspconfig/>`_ a standard configuration might look something like the following

.. code-block:: lua

   lspconfig.esbonio.setup{
     capabilities = capabilities,
     cmd = { "esbonio" },
     filetypes = {"rst"},
     init_options = {
       server = {
         logLevel = "debug"
       },
       sphinx = {
         buildDir = "${confDir}/_build"
       }
     },
     on_attach = on_attach,
   }

To update this to launch the server via the agent, we need only modify the ``cmd`` field (or add one if it does not exist) to include ``lsp-devtools agent --``

.. code-block:: diff

     lspconfig.esbonio.setup{
       capabilities = capabilities,
   -   cmd = { "esbonio" },
   +   cmd = { "lsp-devtools", "agent", "--", "esbonio" },
       ...
     }

Server Applications
-------------------

Once you have your client configured, you need to start the application the agent is going to try to connect to.
Currently ``lsp-devtools`` provides the following applications

``lsp-devtools record``
   As the name suggests, this command supports recording all (or a subset of) messages in a LSP session to a text file or SQLite database.
   However, it can also print these messages direct to the console with support for filtering and custom formatting of message contents.

   .. figure:: /images/record-example.svg

   See :doc:`/lsp-devtools/guide/record-command` for details

``lsp-devtools tui``
   An interactive terminal application, powered by `textual <https://pypi.org/project/textual>`_.

   .. figure:: /images/tui-screenshot.svg

   See :doc:`/lsp-devtools/guide/tui-command` for details
