import inspect
import logging
import sys
import textwrap
import typing
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional

import attrs
import pytest
import pytest_asyncio
from pygls.client import JsonRPCClient

from pytest_lsp.client import LanguageClient
from pytest_lsp.client import make_test_lsp_client

logger = logging.getLogger("client")


@attrs.define
class ClientServerConfig:
    """Configuration for a Client-Server connection."""

    server_command: List[str]
    """The command to use to start the language server."""

    client_factory: Callable[[], JsonRPCClient] = attrs.field(
        default=make_test_lsp_client,
    )
    """Factory function to use when constructing the test client instance."""

    server_env: Optional[Dict[str, str]] = attrs.field(default=None)
    """Environment variables to set when starting the server."""

    async def start(self) -> JsonRPCClient:
        """Return the client instance to use for the test."""
        client = self.client_factory()

        await client.start_io(*self.server_command, env=self.server_env)
        return client


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
    client: JsonRPCClient,
    request: pytest.FixtureRequest,
) -> dict:
    """Return the arguments to pass to the user's fixture function.

    Parameters
    ----------
    fn
       The user's fixture function

    client
       The test client instance to inject

    request
       pytest's request fixture

    Returns
    -------
    dict
       The set of arguments to pass to the user's fixture function
    """
    kwargs: Dict[str, Any] = {}
    required_parameters = set(inspect.signature(fn).parameters.keys())

    # Inject the 'request' fixture if requested
    if "request" in required_parameters:
        kwargs["request"] = request
        required_parameters.remove("request")

    # Inject the language client
    for name, cls in typing.get_type_hints(fn).items():
        if issubclass(cls, JsonRPCClient):
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
            client = await config.start()

            kwargs = get_fixture_arguments(fn, client, request)
            result = fn(**kwargs)
            if inspect.isasyncgen(result):
                try:
                    await anext(result)
                except StopAsyncIteration:
                    pass

            yield client

            if inspect.isasyncgen(result):
                try:
                    await anext(result)
                except StopAsyncIteration:
                    pass

            await client.stop()

        return the_fixture

    if fixture_function:
        return wrapper(fixture_function)

    return wrapper
