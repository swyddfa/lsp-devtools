Client Capabilities
===================

The
`initialize <https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#initialize>`_
request at the start of an LSP session allows the client and server to exchange information about each other.
Of particular interest is the
`ClientCapabilities <https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#clientCapabilities>`_
field which is used to inform the server which parts of the specification the client supports.

Setting this field to the right value ``pytest-lsp`` can pretend to be a particular editor at a particular version and check to see if the server adapts accordingly.

.. _pytest-lsp-supported-clients:

Supported Clients
-----------------

``pytest-lsp`` currently supports the following clients and versions.

.. supported-clients::

The :func:`~pytest_lsp.client_capabilities` function can be used to load the capabilities corresponding to a given client name

.. literalinclude:: ../../../lib/pytest-lsp/tests/examples/client-capabilities/t_server.py
   :language: python
   :start-at: @pytest_lsp.fixture
   :end-at: await lsp_client.shutdown_session()

.. _pytest-lsp-spec-checks:

Specification Compliance Checks
-------------------------------

By setting the client's capabilities to anything other than ``ClientCapabilities()``, ``pytest-lsp`` will automatically enable checks to ensure that the server respects the capabilities published by the client.
If any issues are found, ``pytest-lsp`` will emit an :class:`~pytest_lsp.checks.LspSpecificationWarning`.

.. tip::

   For full details on the checks that have been implemented see the :mod:`pytest_lsp.checks` module.


As an example, let's write a test for the following language server.

.. literalinclude:: ../../../lib/pytest-lsp/tests/examples/client-capabilities/server.py
   :language: python
   :start-at: @server.feature
   :end-at: ]

When it receives a completion request it returns a single item called ``greet`` which, when selected, expands into a snippet making it easier to type the sequence ``"Hello, world!"``.
Let's write a test to confirm it works as expected.

.. literalinclude:: ../../../lib/pytest-lsp/tests/examples/client-capabilities/t_server.py
   :language: python
   :start-at: async def test_completions

Running this test while pretending to be ``neovim`` we should see that while it passes, ``pytest-lsp`` will emit a warning saying that neovim does not support snippets.

.. note::

   *Vanilla* Neovim v0.6.1 does not support snippets, though there are many plugins that can be installed to enable support for them.

.. literalinclude:: ./client-capabilities-output.txt
   :language: none

Strict Checks
^^^^^^^^^^^^^

You can upgrade these warnings to be errors if you wish by passing ``-W error::pytest_lsp.LspSpecificationWarning`` to pytest.

.. literalinclude:: ./client-capabilities-error.txt
   :language: none

Disabling Checks
^^^^^^^^^^^^^^^^

Alternatively, you can ignore these warnings by passing ``-W ignore::pytest_lsp.LspSpecificationWarning`` to pytest.

.. literalinclude:: ./client-capabilities-ignore.txt
   :language: none


.. seealso::

   :ref:`pytest:controlling-warnings`
      Pytest's documentation on configuring how warnings should be handled

   :ref:`python:warning-filter`
      Python's built in warning filter syntax
