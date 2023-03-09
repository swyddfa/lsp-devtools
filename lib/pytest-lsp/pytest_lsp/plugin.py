import asyncio
import inspect
import json
import logging
import os
import subprocess
import sys
import textwrap
import threading
from concurrent.futures import ThreadPoolExecutor
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
from pygls.server import StdOutTransportAdapter
from pygls.server import aio_readline

from pytest_lsp.client import LanguageClient
from pytest_lsp.client import make_test_client

if sys.version_info.minor < 9:
    import importlib_resources as resources
else:
    import importlib.resources as resources  # type: ignore[no-redef]


logger = logging.getLogger("client")


async def check_server_process(
    server: subprocess.Popen, stop: threading.Event, client: LanguageClient
):
    """Continously poll server process to see if it is still running."""
    while not stop.is_set():
        retcode = server.poll()
        if retcode is not None:
            stderr = ""
            if server.stderr is not None:
                stderr = server.stderr.read().decode("utf8")

            message = f"Server exited with return code: {retcode}\n{stderr}"
            client._report_server_error(RuntimeError(message), RuntimeError)

        else:
            await asyncio.sleep(0.1)


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
        self.server = server
        """The process object running the server."""

        self.client = client
        """The client used to drive the test."""

        self.client_capabilities = client_capabilities
        """The capabilities of the client."""

        self.initialization_options = initialization_options
        """The initialization options to pass to the server."""

        self.root_uri = root_uri
        """The root uri to point the server at."""

        self._thread_pool_executor = ThreadPoolExecutor(max_workers=2)
        self._stop_event = threading.Event()

    async def start(self):
        loop = asyncio.get_running_loop()

        self.client._stop_event = self._stop_event
        transport = StdOutTransportAdapter(self.server.stdout, self.server.stdin)
        self.client.lsp.connection_made(transport)

        # TODO: Remove once Python 3.7 is no longer supported
        conn_name = {}
        watch_name = {}

        if sys.version_info.minor > 7:
            conn_name["name"] = "Client-Server Connection"
            watch_name["name"] = "Server Watchdog"

        # Have the client listen to and respond to requests from the server.
        self.conn = loop.create_task(
            aio_readline(
                loop,
                self._thread_pool_executor,
                self.client._stop_event,
                self.server.stdout,
                self.client.lsp.data_received,
            ),
            **conn_name,  # type: ignore[arg-type]
        )

        # Watch the server process to see if it exits prematurely.
        self.watch = loop.create_task(
            check_server_process(self.server, self._stop_event, self.client),
            **watch_name,  # type: ignore[arg-type]
        )

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
            self.server.terminate()

        if self.client._stop_event:
            self.client._stop_event.set()

        # Wait for background tasks to finish.
        await asyncio.gather(self.conn, self.watch)


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


@pytest.hookimpl(trylast=True)
def pytest_runtest_setup(item: pytest.Item):
    """Ensure that that client has not errored before running a test."""

    client: Optional[LanguageClient] = None
    for arg in item.funcargs.values():  # type: ignore[attr-defined]
        if isinstance(arg, LanguageClient):
            client = arg
            break

    if not client or client.error is None:
        return

    raise client.error


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
