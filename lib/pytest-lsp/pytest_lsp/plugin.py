import inspect
import logging
import sys
import textwrap
import typing
from typing import Callable
from typing import List
from typing import Optional

import pytest
import pytest_asyncio

from pytest_lsp.client import LanguageClient
from pytest_lsp.client import make_test_client

logger = logging.getLogger("client")


class ClientServer:
    """A client server pair used to drive test cases."""

    def __init__(self, *, client: LanguageClient, server_command: List[str]):
        self.server_command = server_command
        """The command to use when starting the server."""

        self.client = client
        """The client used to drive the test."""

    async def start(self):
        await self.client.start_io(*self.server_command)

    async def stop(self):
        await self.client.stop()


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

    return ClientServer(
        server_command=config.server_command,
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


def get_fixture_arguments(
    fn: Callable,
    client: LanguageClient,
    request: pytest.FixtureRequest,
) -> dict:
    """Return the arguments to pass to the user's fixture function.

    Parameters
    ----------
    fn
       The user's fixture function

    client
       The language client instance to inject

    request
       pytest's request fixture

    Returns
    -------
    dict
       The set of arguments to pass to the user's fixture function
    """
    kwargs = {}
    required_parameters = set(inspect.signature(fn).parameters.keys())

    # Inject the 'request' fixture if requested
    if "request" in required_parameters:
        kwargs["request"] = request
        required_parameters.remove("request")

    # Inject the language client
    for name, cls in typing.get_type_hints(fn).items():
        if issubclass(cls, LanguageClient):
            kwargs[name] = client
            required_parameters.remove(name)

    # Assume all remaining parameters are pytest fixtures
    for name in required_parameters:
        kwargs[name] = request.getfixturevalue(name)

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
            await client_server.start()

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
