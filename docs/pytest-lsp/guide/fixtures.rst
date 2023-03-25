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
