Troubleshooting
===============

My tests won't run!
-------------------

You may encounter an issue where some of your test cases that use ``pytest-lsp`` are unexpectedly skipped.

.. code-block:: none

   ================================ test session starts =================================
   platform linux -- Python 3.10.6, pytest-7.3.2, pluggy-1.1.0
   rootdir: /home/username/projects/lsp/pytest-lsp
   plugins: lsp-0.3.0, typeguard-3.0.2, asyncio-0.21.0
   asyncio: mode=strict
   collected 1 item

   test_server.py s                                                               [100%]

   ================================== warnings summary ==================================
   test_server.py::test_completions
     /home/username/projects/lsp/pytest-lsp/venv/lib/python3.10/site-packages/_pytest/python.py:183: PytestUnhandledCoroutineWarning: async def functions are not natively supported and have been skipped.
     You need to install a suitable plugin for your async framework, for example:
       - anyio
       - pytest-asyncio
       - pytest-tornasync
       - pytest-trio
       - pytest-twisted
       warnings.warn(PytestUnhandledCoroutineWarning(msg.format(nodeid)))

   =========================== 1 skipped, 1 warning in 0.64s ============================

It's likely that you forgot to add a ``@pytest.mark.asyncio`` marker to your test function(s)

.. code-block:: python

   import pytest

   @pytest.mark.asyncio
   async def test_server(client: LanguageClient):
      ...

Alternatively, if you prefer, you can set the following configuration option in your project's ``pyproject.toml``

.. code-block:: toml

   [tool.pytest.ini_options]
   asyncio_mode = "auto"

In which case `pytest-asyncio`_ will automatically collect and run any ``async`` test function in your test suite.

``ScopeMismatch`` Error
-----------------------

Setting your client `fixture's scope <https://docs.pytest.org/en/7.1.x/how-to/fixtures.html#scope-sharing-fixtures-across-classes-modules-packages-or-session>`__ to something like ``session`` will allow you to reuse the same client-server connection across multiple test cases.
However, you're likely to encounter an error like the following::

  __________________________ ERROR at setup of test_capabilities _________________________
  ScopeMismatch: You tried to access the function scoped fixture event_loop with a session
  scoped request object, involved factories:
  /.../site-packages/pytest_lsp/plugin.py:201:  def the_fixture(request)


This is due to the default `event_loop <https://pytest-asyncio.readthedocs.io/en/latest/reference/fixtures.html#event-loop>`__ fixture provided by `pytest-asyncio`_ not living long enough to support your client.
To fix this you can override the ``event_loop`` fixture, setting its scope to match that of your client.

.. code-block:: python

   @pytest.fixture(scope="session")
   def event_loop():
       """Redefine `pytest-asyncio's default event_loop fixture to match the scope
       of our client fixture."""
       policy = asyncio.get_event_loop_policy()
       loop = policy.new_event_loop()
       yield loop
       loop.close()


.. _pytest-asyncio: https://github.com/pytest-dev/pytest-asyncio

``DeprecationWarning``: Unclosed event loop
-------------------------------------------

Depending on the version of ``pygls`` (the LSP implementation used by ``pytest-lsp``) you have installed, you may encounter a ``DeprecationWarning`` abount an unclosed event loop.

.. code-block:: none

   ================================ test session starts =================================
   platform linux -- Python 3.10.6, pytest-7.3.2, pluggy-1.1.0
   rootdir: /home/username/projects/lsp/pytest-lsp
   plugins: lsp-0.3.0, typeguard-3.0.2, asyncio-0.21.0
   asyncio: mode=strict
   collected 1 item

   test_server.py .                                                               [100%]

   ================================== warnings summary ==================================
   test_server.py::test_completions
     /home/username/projects/lsp/pytest-lsp/venv/lib/python3.10/site-packages/pytest_asyncio/plugin.py:444: DeprecationWarning: pytest-asyncio detected an unclosed event loop when tearing down the event_loop
     fixture: <_UnixSelectorEventLoop running=False closed=False debug=False>
     pytest-asyncio will close the event loop for you, but future versions of the
     library will no longer do so. In order to ensure compatibility with future
     versions, please make sure that:
         1. Any custom "event_loop" fixture properly closes the loop after yielding it
         5. Your code does not modify the event loop in async fixtures or tests

       warnings.warn(

   -- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
   =========================== 1 passed, 1 warning in 0.64s =============================

This is a known issue in ``pygls v1.0.2`` and older, upgrading your ``pygls`` version to ``1.1.0`` or newer should resolve the issue.

.. note::

   While this issue has been `fixed <https://github.com/openlawlibrary/pygls/pull/336>`_ upstream, it is not yet generally available.
   However, the warning itself is fairly mild - ``pytest-lsp``/``pygls`` are not cleaning the event loop up correctly but are otherwise working as expected.
   It should be safe to ignore this while waiting for the fix to become available.
