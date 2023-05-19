import asyncio
import inspect
import logging
import subprocess
import sys
import textwrap
import threading
import typing
from concurrent.futures import ThreadPoolExecutor
from typing import Callable
from typing import List
from typing import Optional

import pytest
import pytest_asyncio
from pygls.server import StdOutTransportAdapter
from pygls.server import aio_readline

from pytest_lsp.client import LanguageClient
from pytest_lsp.client import make_test_client

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

    def __init__(self, *, client: LanguageClient, server: subprocess.Popen):
        self.server = server
        """The process object running the server."""

        self.client = client
        """The client used to drive the test."""

        self._thread_pool_executor = ThreadPoolExecutor(max_workers=2)
        self._stop_event = threading.Event()

    def start(self):
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

    async def stop(self):
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
        *,
        client_factory: Callable[[], LanguageClient] = make_test_client,
    ) -> None:
        """
        Parameters
        ----------
        server_command
           The command to use to start the language server.

        client_factory
           Factory function to use when constructing the language client instance.
           Defaults to :func:`pytest_lsp.make_test_client`
        """

        self.server_command = server_command
        self.client_factory = client_factory


def make_client_server(config: ClientServerConfig) -> ClientServer:
    """Construct a new ``ClientServer`` instance."""

    server = subprocess.Popen(
        config.server_command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    return ClientServer(
        server=server,
        client=config.client_factory(),
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

    levels = ["ERROR: ", " WARN: ", " INFO: ", "  LOG: "]

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


# anext() was added in 3.10
if sys.version_info.minor < 10:

    async def anext(it):
        return await it.__anext__()


def get_fixture_arguments(fn: Callable, client: LanguageClient, request) -> dict:
    """Return the arguments to pass to the user's fixture function"""
    kwargs = {}

    parameters = inspect.signature(fn).parameters
    if "request" in parameters:
        kwargs["request"] = request

    for name, cls in typing.get_type_hints(fn).items():
        if issubclass(cls, LanguageClient):
            kwargs[name] = client

    return kwargs


def fixture(
    fixture_function=None,
    *,
    config: ClientServerConfig,
    **kwargs,
):
    """Define a fixture that returns a client connected to a server running in a
    background sub-process

    Parameters
    ----------
    config
       Configuration for the client and server.
    """

    def wrapper(fn):
        @pytest_asyncio.fixture(**kwargs)
        async def the_fixture(request):
            client_server = make_client_server(config)
            client_server.start()

            kwargs = get_fixture_arguments(fn, client_server.client, request)
            result = fn(**kwargs)
            if inspect.isasyncgen(result):
                try:
                    await anext(result)
                except StopAsyncIteration:
                    pass

            yield client_server.client

            if inspect.isasyncgen(result):
                try:
                    await anext(result)
                except StopAsyncIteration:
                    pass

            await client_server.stop()

        return the_fixture

    if fixture_function:
        return wrapper(fixture_function)

    return wrapper
