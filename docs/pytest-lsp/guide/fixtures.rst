Fixtures
========

.. highlight:: none

Parameterised Fixtures
----------------------

Like regular pytest fixtures, :func:`pytest_lsp.fixture` supports `parameterisation <https://docs.pytest.org/en/7.1.x/how-to/fixtures.html#parametrizing-fixtures>`__.
This can be used to run the same set of tests while pretending to be a different client each time.

.. literalinclude:: ../../../lib/pytest-lsp/tests/examples/parameterised-clients/t_server.py
   :language: python
   :start-at: @pytest_lsp.fixture
   :end-at: await lsp_client.shutdown_session()


Requesting Other Fixtures
-------------------------

As you would expect, it's possible to request other fixtures to help set up your client.

.. literalinclude:: ../../../lib/pytest-lsp/tests/examples/fixture-passthrough/t_server.py
   :language: python
   :start-at: @pytest.fixture
   :end-at: await lsp_client.shutdown_session()
