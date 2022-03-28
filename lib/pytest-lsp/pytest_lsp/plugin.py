import asyncio
import inspect
import json
import logging
import os
import subprocess
import threading
from typing import Any
from typing import Callable
from typing import Iterable
from typing import List
from typing import Optional
from typing import Union

import pytest
import pytest_asyncio
from pygls.lsp.methods import EXIT
from pygls.lsp.methods import INITIALIZE
from pygls.lsp.methods import INITIALIZED
from pygls.lsp.methods import SHUTDOWN
from pygls.lsp.types import ClientCapabilities
from pygls.lsp.types import InitializeParams

from pytest_lsp.client import Client
from pytest_lsp.client import make_test_client

try:
    import importlib.resources as resources
except ImportError:
    import importlib_resources as resources


logger = logging.getLogger("client")


if hasattr(pytest_asyncio, "fixture"):
    make_fixture = pytest_asyncio.fixture
else:
    make_fixture = pytest.fixture


class ClientServer:
    """A client server pair used to drive test cases."""

    def __init__(
        self,
        client: Client,
        server: subprocess.Popen,
        root_uri: str,
        client_capabilities: ClientCapabilities,
        initialization_options: Optional[Any],
    ):

        self._server = server
        """The process object running the server."""

        self.client = client
        """The client used to drive the test."""

        self.client_capabilities = client_capabilities
        """The capabilities of the client."""

        self._client_thread = threading.Thread(
            name="Client Thread",
            target=self.client.start_io,
            args=(self._server.stdout, self._server.stdin),
        )
        self._client_thread.daemon = True

        self.initialization_options = initialization_options
        """The initialization options to pass to the server."""

        self.root_uri = root_uri
        """The root uri to point the server at."""

    async def start(self):
        self._client_thread.start()

        # Give the client some time to initialize
        while self.client.lsp.transport is None:
            await asyncio.sleep(0.1)

        response = await self.client.lsp.send_request_async(
            INITIALIZE,
            InitializeParams(
                process_id=os.getpid(),
                root_uri=self.root_uri,
                capabilities=self.client_capabilities,
                initialization_options=self.initialization_options or {},
            ),
        )

        assert "capabilities" in response
        self.client.lsp.notify(INITIALIZED)

        return

    async def stop(self):
        response = await self.client.lsp.send_request_async(SHUTDOWN)
        assert response is None

        self.client.lsp.notify(EXIT)

        self.client._stop_event.set()
        try:
            self.client.loop._signal_handlers.clear()
        except AttributeError:
            pass

        self._client_thread.join()


class ClientServerConfig:
    """Configuration for a LSP Client-Server pair."""

    def __init__(
        self,
        server_command: List[str],
        root_uri: str,
        *,
        client: str = "",
        client_capabilities: Optional[ClientCapabilities] = None,
        client_factory: Callable = make_test_client,
        initialization_options: Optional[Any] = None,
    ) -> None:

        self.server_command: List[str] = server_command
        """The command to use to start the language server."""

        self.root_uri: str = root_uri
        """The root uri to start the language server in"""

        self.client: str = client
        """The name of the client profile to use"""

        self.client_capabilities: Optional[ClientCapabilities] = client_capabilities
        """Use to use a specific set of client, capabilities. The setting overrides
        ``client``."""

        self.client_factory: Callable = client_factory
        """The function to use to return a test client instance."""

        self.initialization_options = initialization_options
        """The initialization options to pass to the server on start up."""


def find_client_capabilities(client: str) -> ClientCapabilities:
    """Find the capabilities that correspond to the given client spec."""

    # Currently, we only have a single version of each client so let's just return the
    # first one we find.
    #
    # TODO: Implement support for client@x.y.z
    # TODO: Implement support for client@latest?
    filename = None
    for resource in resources.files("pytest_lsp.clients").iterdir():

        # Skip the README or any other files that we don't care about.
        if not resource.name.endswith(".json"):
            continue

        if resource.name.startswith(client.replace("-", "_")):
            filename = resource
            break

    if not filename:
        raise ValueError(f"Unsupported client '{client}'")

    return ClientCapabilities(**json.loads(filename.read_text()))


def make_client_server(config: ClientServerConfig) -> ClientServer:
    """Construct a new ``ClientServer`` instance."""

    server = subprocess.Popen(
        config.server_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE
    )

    if config.client_capabilities:
        capabilities = config.client_capabilities
    elif config.client:
        capabilities = find_client_capabilities(config.client)
    else:
        capabilities = ClientCapabilities()

    return ClientServer(
        client=config.client_factory(capabilities, config.root_uri),
        server=server,
        client_capabilities=capabilities,
        root_uri=config.root_uri,
        initialization_options=config.initialization_options,
    )


def fixture(
    fixture_function=None,
    *,
    config: Union[ClientServerConfig, Iterable[ClientServerConfig]],
    **kwargs,
):

    if isinstance(config, ClientServerConfig):
        config = [config]

    def wrapper(fn):
        @make_fixture(params=config, **kwargs)
        async def the_fixture(request):

            lsp = make_client_server(request.param)
            await lsp.start()

            # TODO: Do this 'properly'
            signature = inspect.signature(fn)
            if "client_" in signature.parameters.keys():
                await fn(lsp.client)
            else:
                await fn()

            yield lsp.client
            await lsp.stop()

        return the_fixture

    if fixture_function:
        return wrapper(fixture_function)

    return wrapper
