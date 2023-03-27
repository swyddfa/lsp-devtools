Fixtures
========

.. highlight:: none

Fixture Scope
-------------

Setting your client `fixture's scope <https://docs.pytest.org/en/7.1.x/how-to/fixtures.html#scope-sharing-fixtures-across-classes-modules-packages-or-session>`__ to something like ``session`` will allow you to reuse the same client-server connection across multiple test cases.
However, you're likely to encounter an error like the following::

  __________________________ ERROR at setup of test_capabilities _________________________
  ScopeMismatch: You tried to access the function scoped fixture event_loop with a session
  scoped request object, involved factories:
  /.../site-packages/pytest_lsp/plugin.py:201:  def the_fixture(request)


This is due to the default `event_loop <https://pytest-asyncio.readthedocs.io/en/latest/reference/fixtures.html#event-loop>`__ fixture provided by `pytest-asyncio`_ not living long enough to support your client.
To fix this you can override the ``event_loop`` fixture, setting its scope to match that of your client.

.. literalinclude:: ../../../lib/pytest-lsp/tests/test_client_methods.py
   :language: python
   :start-at: @pytest.fixture(scope="session")
   :end-at: loop.close()

.. _pytest-asyncio: https://github.com/pytest-dev/pytest-asyncio


Parameterised Fixtures
----------------------

Like regular pytest fixtures, :func:`pytest_lsp.fixture` supports `parameterisation <https://docs.pytest.org/en/7.1.x/how-to/fixtures.html#parametrizing-fixtures>`__.
This can be used to run the same set of tests while pretending to be a different client each time.

.. literalinclude:: ../../../lib/pytest-lsp/tests/examples/parameterised-clients/t_server.py
   :language: python
   :start-at: @pytest_lsp.fixture
   :end-at: await lsp_client.shutdown()
