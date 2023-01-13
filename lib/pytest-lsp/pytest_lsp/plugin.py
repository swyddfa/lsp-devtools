import asyncio
import inspect
import json
import logging
import os
import subprocess
import sys
import textwrap
import threading
import time
from typing import Any
from typing import Callable
from typing import Iterable
from typing import List
from typing import Optional
from typing import Union

import pytest
import pytest_asyncio
from lsprotocol.converters import get_converter
from lsprotocol.types import ClientCapabilities
from lsprotocol.types import InitializedParams
from lsprotocol.types import InitializeParams
from lsprotocol.types import LSPAny
from pytest_lsp.client import LanguageClient
from pytest_lsp.client import make_test_client

if sys.version_info.minor < 9:
    import importlib_resources as resources
else:
    import importlib.resources as resources  # type: ignore[no-redef]


logger = logging.getLogger("client")


def watch_server_process(
    server: subprocess.Popen, stop: threading.Event, client: LanguageClient
):
    """Continously poll server process to see if it is still running."""
    while True:
        retcode = server.poll()

        if stop.is_set():
            break

        if retcode is not None:

            stderr = ""
            if server.stderr is not None:
                stderr = server.stderr.read().decode("utf8")

            message = f"Server exited with return code: {retcode}\n{stderr}"
            client._report_server_error(RuntimeError(message), RuntimeError)
            break

        time.sleep(0.1)


class ClientServer:
    """A client server pair used to drive test cases."""

    def __init__(
        self,
        client: LanguageClient,
        server: subprocess.Popen,
        root_uri: str,
        client_capabilities: ClientCapabilities,
        initialization_options: Optional[LSPAny],
    ):

        self._server = server
        """The process object running the server."""

        control_loop = asyncio.get_running_loop()

        self.client = client
        self.client._control_loop = control_loop
        """The client used to drive the test."""

        self.client_capabilities = client_capabilities
        """The capabilities of the client."""

        self._client_thread = threading.Thread(
            name="Client Thread",
            target=self.client.start_io,
            args=(self._server.stdout, self._server.stdin),
            daemon=True,
        )

        # Used to detect if the server crashes.
        self._watchdog_stop = threading.Event()
        self._watchdog_thread = threading.Thread(
            name="Watchdog Thread",
            target=watch_server_process,
            args=(self._server, self._watchdog_stop, self.client),
            daemon=True,
        )

        self.initialization_options = initialization_options
        """The initialization options to pass to the server."""

        self.root_uri = root_uri
        """The root uri to point the server at."""

    async def start(self):
        self._watchdog_thread.start()
        self._client_thread.start()

        # Give the client some time to initialize
        while self.client.lsp.transport is None:
            await asyncio.sleep(0.1)

        response = await self.client.initialize_request(
            InitializeParams(
                process_id=os.getpid(),
                root_uri=self.root_uri,
                capabilities=self.client_capabilities,
                initialization_options=self.initialization_options,
            ),
        )

        assert response.capabilities is not None
        self.client.notify_initialized(InitializedParams())

        return response

    async def stop(self):

        # Only attempt if there wasn't an error.
        if self.client.error is None:
            response = await self.client.shutdown_request(None)  # type: ignore
            assert response is None

            self.client.notify_exit(None)
        else:
            self._server.terminate()

        if self.client._stop_event:
            self.client._stop_event.set()

        try:
            self.client.loop._signal_handlers.clear()  # type: ignore
        except AttributeError:
            pass

        self._watchdog_stop.set()
        self._watchdog_thread.join()

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
        client_factory: Callable[..., LanguageClient] = make_test_client,
        initialization_options: Optional[Any] = None,
    ) -> None:
        """
        Parameters
        ----------
        server_command
           The command to use to start the language server.

        root_uri
           The root uri to start the language server in

        client
           The name of the client profile to use

        client_capabilities
           Use to use a specific set of client, capabilities.
           Specifiying this will override ``client``.

        client_factory
           Factory function to use when constructing the language client instance.
           Defaults to :func:`pytest_lsp.make_test_client`

        initialization_options
           The initialization options to pass to the server on start up.

        """

        self.server_command = server_command
        self.root_uri = root_uri
        self.client = client
        self.client_capabilities = client_capabilities
        self.client_factory = client_factory
        self.initialization_options = initialization_options


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

    converter = get_converter()
    capabilities = json.loads(filename.read_text())
    return converter.structure(capabilities, ClientCapabilities)


def make_client_server(config: ClientServerConfig) -> ClientServer:
    """Construct a new ``ClientServer`` instance."""

    server = subprocess.Popen(
        config.server_command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if config.client_capabilities:
        capabilities = config.client_capabilities
    elif config.client:
        capabilities = find_client_capabilities(config.client)
    else:
        capabilities = ClientCapabilities()

    client = config.client_factory(capabilities, config.root_uri)

    return ClientServer(
        client=client,
        server=server,
        client_capabilities=capabilities,
        root_uri=config.root_uri,
        initialization_options=config.initialization_options,
    )


def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    """Add any captured log messages to the report."""
    client: Optional[LanguageClient] = None

    if not hasattr(item, "funcargs"):
        return

    for arg in item.funcargs.values():
        if isinstance(arg, LanguageClient):
            client = arg
            break

    if not client:
        return

    levels = ["ERROR: ", " WARN: ", " INFO: ", "DEBUG: "]

    if call.when == "setup":
        captured_messages = client.log_messages[: client._setup_log_index + 1]
    else:
        captured_messages = client.log_messages[client._last_log_index :]
        client._last_log_index = len(client.log_messages)

    messages = [
        f"{textwrap.indent(m.message, levels[m.type.value - 1])}"
        for m in captured_messages
    ]

    if len(messages) > 0:
        item.add_report_section(call.when, "window/logMessages", "\n".join(messages))


def fixture(
    fixture_function=None,
    *,
    config: Union[ClientServerConfig, Iterable[ClientServerConfig]],
    **kwargs,
):

    if isinstance(config, ClientServerConfig):
        params = [config]
    else:
        params = list(config)

    ids = [conf.client or f"client{idx}" for idx, conf in enumerate(params)]

    def wrapper(fn):
        @pytest_asyncio.fixture(params=params, ids=ids, **kwargs)
        async def the_fixture(request):

            lsp = make_client_server(request.param)
            await lsp.start()

            # TODO: Do this 'properly'
            signature = inspect.signature(fn)
            if "client_" in signature.parameters.keys():
                await fn(lsp.client)
            else:
                await fn()

            lsp.client._setup_log_index = len(lsp.client.log_messages)
            lsp.client._last_log_index = len(lsp.client.log_messages)

            yield lsp.client
            await lsp.stop()

        return the_fixture

    if fixture_function:
        return wrapper(fixture_function)

    return wrapper
