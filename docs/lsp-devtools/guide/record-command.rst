Recording Sessions
==================

.. important::

   This guide assumes that you have already :ref:`configured your client <lsp-devtools-configure-client>` to wrap your language server with the LSP Agent.

.. highlight:: none

.. program:: lsp-devtools record

The ``lsp-devtools record`` command can be used to either record an LSP session to a file, SQLite database or print the received messages direct to the console.
Running the ``lsp-devtools record`` command you should see a message like the following::

  $ lsp-devtools record
  Waiting for connection on localhost:8765...

once the agent connects, the record command will by default, start printing all LSP messages to the console, with the JSON contents pretty printed.

.. figure:: /images/record-example.svg


Example Commands
----------------

Here are some example usages of the ``record`` command that you may find useful.

**Capture the client's capabilities**

The following command will save to a JSON file only the client's info and :class:`pygls:lsprotocol.types.ClientCapabilities` sent during the ``initialize`` request - useful for :ref:`adding clients to pytest-lsp <pytest-lsp-supported-clients>`! 😉


::

   lsp-devtools record -f '{{"clientInfo": {.params.clientInfo}, "capabilities": {.params.capabilities}}}' --to-file <client_name>_v<version>.json

**Format and show any window/logMessages**

This can be used to replicate the ``Output`` log panel in VSCode in editors that do not provide a similar facility.

::

   lsp-devtools record -f "{.params.type|MessageType}: {.params.message}"

.. figure:: /images/record-log-messages.svg
   :figclass: scrollable-svg

Read on for a comprehensive overview of all the available command line options.

Connection Options
------------------

By default, the LSP agent and other commands will attempt to connect to each other on ``localhost:8765``.
The following options can be used to change this behavior

.. option:: --host <host>

   The host to bind to.

.. option:: -p <port>, --port <port>

   The port number to open the connection on.


Alternate Destinations
----------------------

As well as printing to console, the record command supports a number of other output destinations.

.. option:: --to-file <filename>

   Saves all collected messages to a plain text file with each line representing a complete JSON-RPC message::

      lsp-devtools record --to-file example.json

   See :download:`here <./example-to-file-output.json>` for example of the output produced by this command.

.. option:: --to-sqlite <filename>

   Save messages to a SQLite database::

      lsp-devtools record --to-sqlite example.db

   This database can then be opened in other tools like `datasette <https://datasette.io/>`_, `SQLite Browser <https://sqlitebrowser.org/>`_ or even ``lsp-devtools`` own :doc:`/lsp-devtools/guide/inspect-command`.

   .. dropdown:: DB Schema

      Here is the schema currently used by ``lsp-devtools``.
      **Note:** Except perhaps the base ``protocol`` table, this schema is not stable and may change between ``lsp-devtools`` releases.

      .. literalinclude:: ../../../lib/lsp-devtools/lsp_devtools/handlers/dbinit.sql
         :language: sql

.. option:: --save-output <filename>

   Print to console as normal but additionally, the ouput will be saved into a text file using the
   `export <https://rich.readthedocs.io/en/stable/console.html#exporting>`__
   feature of rich's ``Console`` object::

     lsp-devtools record --save-output filename.{html,svg,txt}

   Depending on the file extension used, this will save the output as plain text or rendered as an SVG image or HTML webpage - useful for generating screenshots for your documentation!

Filtering Messages
------------------

Once it gets going, the LSP protocol can generate *a lot* of messages!
To help you focus on the messages you are interested in the ``record`` command provides the following options for selecting a subset of messages to show.

.. option:: --message-source <source>

   The following values are accepted

   ``client``
      Only show messages sent from the client

   ``server``
      Only show messages sent from the server

   ``both`` (the default)
      Show message sent from both client and server

.. option:: --include-message-type <type>

   Only show messages of the given type.
   This option can be used more than once to select multiple message types.
   The following values are accepted

   ``request``
      Show only JSON-RPC request messages

   ``response``
      Show only JSON-RPC response messages, matches responses containing either successful results or error codes.

   ``result``
      Show only JSON-RPC response messages containing successful results

   ``error``
      Show only JSON-RPC response messages that contain errors.

   ``notification``
      Show only JSON-RPC notification messages

.. option:: --include-method <method>

   Only show messages with the given method name.
   This option can be used more than once to select multiple methods.

.. option:: --exclude-message-type <type>

   Like :option:`--include-message-type`, but omit matches rather than showing them

.. option:: --exclude-method <method>

   Like :option:`--include-method`, but omit matches rather than showing them

If multiple options from this list are used, they will be ANDed together, for example::

  lsp-devtools record --message-source client \
                      --include-message-type request \
                      --include-message-type notification

will only show requests or notifications that have been sent by the client.

Formatting messages
-------------------

.. note::

   These options do not apply when using the :option:`--to-sqlite` option.


.. option:: -f <format>, --format-message <format>

   Set the format string to use when formatting messages.
   By default, the ``record`` command will simply print the JSON contents of a message however, you can supply a custom format string to use instead.

   .. tip::

      Format strings are also a powerful filtering mechanism! - any messages that do not fit with the supplied format will not be shown

   Format strings use the following syntax

   .. admonition:: Feedback Wanted!

      We're looking for feedback on this syntax, especially when it comes to formatting lists of items.
      Let us know by `opening an issue <https://github.com/swyddfa/lsp-devtools/issues/new>`_ if you have any thoughts or suggested improvements


   Similar to Python's :ref:`python:formatstrings` a pair of braces (``{}``) denote a placeholder where a value can be inserted.
   Inside the braces you can then select and the message field you want to be inserted using a dot-separated syntax that should feel familiar if you've ever used `jq <https://jqlang.github.io/jq/>`_::

     Message:
     {
       "method": "textDocument/completion",
       "params": {
         "position": {"line": 1, "character": 2},
         "textDocument": {"uri": "file:///path/to/file.txt"},
       }
     }

     Format String:
     "{.params.position.line}:{.params.position.character}"

     Result:
     1:2

   The pipe symbol (``|``) can be used to pass the selected field to a formatter e.g. ``Position``::

     Message:
     {
       "method": "textDocument/completion",
       "params": {
         "position": {"line": 1, "character": 2},
         "textDocument": {"uri": "file:///path/to/file.txt"},
       }
     }

     Format String:
     "{.params.position|Position}"

     Result:
     1:2

   See :ref:`lsp-devtools-record-formatters` for details on all available formatters.
   Fields that contain an array of items can be accessed with square brackets (``[]``), by default items in an array will be separated by newlines when formatted::

     Message:
     {
       "result": {
         "items": [{"label": "one"}, {"label": "two"}, {"label": "three"}]
       }
     }

     Format String:
     "{.result.items[].label}"

     Result:
     one
     two
     three

   However, you can specify a custom separator inside the brackets::

     Message:
     {
       "result": {
         "items": [{"label": "one"}, {"label": "two"}, {"label": "three"}]
       }
     }

     Format String:
     "{.result.items[\n- ].label}"

     Result:
     - one
     - two
     - three

   The brackets also support Python's standard list indexing rules::

     Message:
     {
       "result": {
         "items": [{"label": "one"}, {"label": "two"}, {"label": "three"}]
       }
     }

     Format String:                  Result:
     "{.result.items[0].label}"      one
     "{.result.items[-1].label}"     three
     "{.result.items[0:2].label}"    "one\ntwo"

   Finally, if you want to supply an index *and* adjust the separator you can separate them with the ``#`` symbol::

     Message:
     {
       "result": {
         "items": [{"label": "one"}, {"label": "two"}, {"label": "three"}]
       }
     }

     Format String:
     "{.result.items[0:2#\n- ].label}"

     Result:
     - one
     - two

.. _lsp-devtools-record-formatters:

Formatters
^^^^^^^^^^

``lsp-devtools`` provides the following formatters

``json`` (default)
  Renders objects as "pretty" JSON, equivalent to ``json.dumps(obj, indent=2)``

``json-compact``
  Renders objects as JSON with no additional formatting, equivalent to ``json.dumps(obj)``

``position``
   ``{"line": 1, "character": 2}`` will be rendered as ``1:2``

``range``
   ``{"start": {"line": 1, "character": 2}, "end": {"line": 3, "character": 4}}`` will be rendered as ``1:2-3:4``


Additionally, any enum type can be used as a formatter, where numbers will be replaced with their corresponding name, for example::

  Format String:
  "{.type|MessageType}"

  Value:          Result:
  {"type": 1}     Error
  {"type": 2}     Warning
  {"type": 3}     Info
  {"type": 4}     Log
