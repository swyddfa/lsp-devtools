import asyncio
import pytest

from .client import Client
from .client import make_test_client
from .plugin import fixture
from .plugin import make_client_server
from .plugin import ClientServer
from .plugin import ClientServerConfig

__version__ = "0.0.3"

__all__ = [
    "Client",
    "ClientServer",
    "ClientServerConfig",
    "fixture",
    "make_client_server",
    "make_test_client",
]


@pytest.fixture(scope="session")
def event_loop():
    # We need to redefine the event_loop fixture to match the scope of our
    # client_server fixture.
    #
    # https://github.com/pytest-dev/pytest-asyncio/issues/68#issuecomment-334083751

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
