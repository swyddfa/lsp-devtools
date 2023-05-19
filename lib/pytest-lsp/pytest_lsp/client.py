import asyncio
import json
import logging
import os
import sys
import traceback
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Type

from lsprotocol.converters import get_converter
from lsprotocol.types import TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS
from lsprotocol.types import WINDOW_LOG_MESSAGE
from lsprotocol.types import WINDOW_SHOW_DOCUMENT
from lsprotocol.types import WINDOW_SHOW_MESSAGE
from lsprotocol.types import ClientCapabilities
from lsprotocol.types import Diagnostic
from lsprotocol.types import InitializedParams
from lsprotocol.types import InitializeParams
from lsprotocol.types import InitializeResult
from lsprotocol.types import LogMessageParams
from lsprotocol.types import PublishDiagnosticsParams
from lsprotocol.types import ShowDocumentParams
from lsprotocol.types import ShowDocumentResult
from lsprotocol.types import ShowMessageParams
from pygls.protocol import default_converter

from .gen import Client
from .protocol import LanguageClientProtocol

if sys.version_info.minor < 9:
    import importlib_resources as resources
else:
    import importlib.resources as resources  # type: ignore[no-redef]


__version__ = "0.3.0"
logger = logging.getLogger(__name__)


class LanguageClient(Client):
    """Used to drive language servers under test."""

    def __init__(self, *args, **kwargs):
        super().__init__("pytest-lsp-client", __version__, *args, **kwargs)

        self.capabilities: Optional[ClientCapabilities] = None
        """The client's capabilities."""

        self.shown_documents: List[ShowDocumentParams] = []
        """Used to keep track of the documents requested to be shown via a
        ``window/showDocument`` request."""

        self.messages: List[ShowMessageParams] = []
        """Holds any received ``window/showMessage`` requests."""

        self.log_messages: List[LogMessageParams] = []
        """Holds any received ``window/logMessage`` requests."""

        self.diagnostics: Dict[str, List[Diagnostic]] = {}
        """Used to hold any recieved diagnostics."""

        self.error: Optional[Exception] = None
        """Indicates if the client encountered an error."""

        self._setup_log_index = 0
        """Used to keep track of which log messages occurred during startup."""

        self._last_log_index = 0
        """Used to keep track of which log messages correspond with which test case."""

    def feature(
        self,
        feature_name: str,
        options: Optional[Any] = None,
    ):
        return self.lsp.fm.feature(feature_name, options)

    def _report_server_error(self, error: Exception, source: Type[Exception]):
        # This may wind up being a mistake, but let's ignore broken pipe errors...
        # If the server process has exited, the watchdog task will give us a better
        # error message.
        if isinstance(error, BrokenPipeError):
            return

        self.error = error
        tb = "".join(traceback.format_exc())

        message = f"{source.__name__}: {error}\n{tb}"

        loop = asyncio.get_running_loop()
        loop.call_soon(cancel_all_tasks, message)

        if self._stop_event:
            self._stop_event.set()

    async def initialize_session(self, params: InitializeParams) -> InitializeResult:
        """Make an ``initialize`` request to a lanaguage server.

        It will also automatically send an ``initialized`` notification once
        the server responds.

        Parameters
        ----------
        params
           The parameters to send to the client.

           The following fields will be automatically set if left blank.

           - ``process_id``: Set to the PID of the current process.

        Returns
        -------
        InitializeResult
           The result received from the client.
        """
        self.capabilities = params.capabilities

        if params.process_id is None:
            params.process_id = os.getpid()

        response = await self.initialize_async(params)
        self.initialized(InitializedParams())

        return response

    async def shutdown_session(self) -> None:
        """Shutdown the server under test.

        Helper method that handles sending ``shutdown`` and ``exit`` messages in the
        correct order.

        .. note::

           This method will not attempt to send these messages if a fatal error has
           occurred.

        """
        if self.error is not None or self.capabilities is None:
            return

        await self.shutdown_request_async(None)
        self.exit(None)

    async def wait_for_notification(self, method: str):
        """Block until a notification with the given method is received.

        Parameters
        ----------
        method
           The notification method to wait for, e.g. ``textDocument/publishDiagnostics``
        """
        return await self.lsp.wait_for_notification_async(method)


def cancel_all_tasks(message: str):
    """Called to cancel all awaited tasks."""

    for task in asyncio.all_tasks():
        if sys.version_info.minor < 9:
            task.cancel()
        else:
            task.cancel(message)


def make_test_client() -> LanguageClient:
    """Construct a new test client instance with the handlers needed to capture
    additional responses from the server."""

    client = LanguageClient(
        protocol_cls=LanguageClientProtocol,
        converter_factory=default_converter,
        loop=asyncio.get_running_loop(),
    )

    @client.feature(TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)
    def publish_diagnostics(client: LanguageClient, params: PublishDiagnosticsParams):
        client.diagnostics[params.uri] = params.diagnostics

    @client.feature(WINDOW_LOG_MESSAGE)
    def log_message(client: LanguageClient, params: LogMessageParams):
        client.log_messages.append(params)

        levels = [logger.error, logger.warning, logger.info, logger.debug]
        levels[params.type.value - 1](params.message)

    @client.feature(WINDOW_SHOW_MESSAGE)
    def show_message(client: LanguageClient, params):
        client.messages.append(params)

    @client.feature(WINDOW_SHOW_DOCUMENT)
    def show_document(
        client: LanguageClient, params: ShowDocumentParams
    ) -> ShowDocumentResult:
        client.shown_documents.append(params)
        return ShowDocumentResult(success=True)

    return client


def client_capabilities(client_spec: str) -> ClientCapabilities:
    """Find the capabilities that correspond to the given client spec.

    Parameters
    ----------
    client_spec
       A string describing the client to load the corresponding
       capabilities for.
    """

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

        if resource.name.startswith(client_spec.replace("-", "_")):
            filename = resource
            break

    if not filename:
        raise ValueError(f"Unknown client: '{client_spec}'")

    converter = get_converter()
    capabilities = json.loads(filename.read_text())
    return converter.structure(capabilities, ClientCapabilities)
