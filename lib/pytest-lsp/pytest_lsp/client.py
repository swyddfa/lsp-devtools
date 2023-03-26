import asyncio
import json
import logging
import os
import sys
import traceback
from concurrent.futures import Future
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Type
from typing import Union

from lsprotocol.converters import get_converter
from lsprotocol.types import CANCEL_REQUEST
from lsprotocol.types import TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS
from lsprotocol.types import WINDOW_LOG_MESSAGE
from lsprotocol.types import WINDOW_SHOW_DOCUMENT
from lsprotocol.types import WINDOW_SHOW_MESSAGE
from lsprotocol.types import ClientCapabilities
from lsprotocol.types import CompletionItem
from lsprotocol.types import CompletionList
from lsprotocol.types import CompletionParams
from lsprotocol.types import DefinitionParams
from lsprotocol.types import DeleteFilesParams
from lsprotocol.types import Diagnostic
from lsprotocol.types import DidChangeTextDocumentParams
from lsprotocol.types import DidCloseTextDocumentParams
from lsprotocol.types import DidOpenTextDocumentParams
from lsprotocol.types import DidSaveTextDocumentParams
from lsprotocol.types import DocumentLink
from lsprotocol.types import DocumentLinkParams
from lsprotocol.types import DocumentSymbol
from lsprotocol.types import DocumentSymbolParams
from lsprotocol.types import ExecuteCommandParams
from lsprotocol.types import FileDelete
from lsprotocol.types import Hover
from lsprotocol.types import HoverParams
from lsprotocol.types import ImplementationParams
from lsprotocol.types import InitializedParams
from lsprotocol.types import InitializeParams
from lsprotocol.types import InitializeResult
from lsprotocol.types import Location
from lsprotocol.types import LocationLink
from lsprotocol.types import LogMessageParams
from lsprotocol.types import LSPAny
from lsprotocol.types import Position
from lsprotocol.types import ProgressToken
from lsprotocol.types import PublishDiagnosticsParams
from lsprotocol.types import Range
from lsprotocol.types import ShowDocumentParams
from lsprotocol.types import ShowDocumentResult
from lsprotocol.types import ShowMessageParams
from lsprotocol.types import SymbolInformation
from lsprotocol.types import TextDocumentContentChangeEvent
from lsprotocol.types import TextDocumentContentChangeEvent_Type1
from lsprotocol.types import TextDocumentContentChangeEvent_Type2
from lsprotocol.types import TextDocumentIdentifier
from lsprotocol.types import TextDocumentItem
from lsprotocol.types import VersionedTextDocumentIdentifier
from pygls.exceptions import JsonRpcMethodNotFound
from pygls.protocol import LanguageServerProtocol
from pygls.protocol import default_converter

from .gen import Client

if sys.version_info.minor < 9:
    import importlib_resources as resources
else:
    import importlib.resources as resources  # type: ignore[no-redef]


logger = logging.getLogger(__name__)


class ClientProtocol(LanguageServerProtocol):
    """An extended protocol class with extra methods that are useful for testing."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._notification_futures = {}

    def _handle_notification(self, method_name, params):
        if method_name == CANCEL_REQUEST:
            self._handle_cancel_notification(params.id)
            return

        future = self._notification_futures.pop(method_name, None)
        if future:
            future.set_result(params)

        try:
            handler = self._get_handler(method_name)
            self._execute_notification(handler, params)
        except (KeyError, JsonRpcMethodNotFound):
            logger.warning("Ignoring notification for unknown method '%s'", method_name)
        except Exception:
            logger.exception(
                "Failed to handle notification '%s': %s", method_name, params
            )

    def wait_for_notification(self, method: str, callback=None):
        future: Future = Future()
        if callback:

            def wrapper(future: Future):
                result = future.result()
                callback(result)

            future.add_done_callback(wrapper)

        self._notification_futures[method] = future
        return future

    def wait_for_notification_async(self, method: str):
        future = self.wait_for_notification(method)
        return asyncio.wrap_future(future)


class LanguageClient(Client):
    """Used to drive language servers under test."""

    def __init__(self, *args, **kwargs):
        self.name = "pytest-test-client"
        self.version = None

        super().__init__(*args, **kwargs)

        self.open_documents: Dict[str, int] = {}
        """Used to keep track of the documents that the client has opened."""

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

    async def completion_request(
        self, uri: str, line: int, character: int
    ) -> Union[List[CompletionItem], CompletionList, None]:
        """Make a ``textDocument/completion`` request.

        Helper method for :meth:`~LanguageClient.text_document_completion_request` that
        reduces the amount of boilerplate required to construct the parameters object.

        Parameters
        ----------
        uri
           The uri of the document to make the completion request from
        line
           The line number to make the completion request from
        character
           The character column to make the completion request from.

        """

        params = CompletionParams(
            text_document=TextDocumentIdentifier(uri=uri),
            position=Position(line=line, character=character),
        )

        return await self.text_document_completion_request(params)

    async def definition_request(
        self, uri: str, line: int, character: int
    ) -> Union[Location, List[Location], List[LocationLink], None]:
        """Make a ``textDocument/definition`` request.

        Helper method for :meth:`~LanguageClient.text_document_definition_request`
        that reduces the amount of boilerplate required to construct the parameters
        object.

        Parameters
        ----------
        uri
           The uri of the document to make the request within.

        line
           The line number to make the definition request from

        character
           The character column to make the definition request from
        """
        params = DefinitionParams(
            text_document=TextDocumentIdentifier(uri=uri),
            position=Position(line=line, character=character),
        )

        return await self.text_document_definition_request(params)

    async def document_link_request(self, uri: str) -> Optional[List[DocumentLink]]:
        """Make a ``textDocument/documentLink`` request

        Helper method for :meth:`~LanguageClient.text_document_document_link_request`
        that reduces the amount of boilerplate required to construct the parameters
        object.

        Parameters
        ----------
        uri
           The uri of the document to make the request for.
        """

        params = DocumentLinkParams(text_document=TextDocumentIdentifier(uri=uri))
        return await self.text_document_document_link_request(params)

    async def document_symbols_request(
        self, uri: str
    ) -> Union[List[SymbolInformation], List[DocumentSymbol], None]:
        """Make a ``textDocument/documentSymbol`` request

        Helper method for :meth:`~LanguageClient.text_document_document_symbol_request`
        that reduces the amount of boilerplate required to construct the parameters
        object.

        Parameters
        ----------
        uri
           The uri of the document to make the request for.
        """

        params = DocumentSymbolParams(text_document=TextDocumentIdentifier(uri=uri))
        return await self.text_document_document_symbol_request(params)

    async def execute_command_request(
        self,
        command: str,
        *args: LSPAny,
        work_done_token: Optional[ProgressToken] = None,
    ):
        """Make a ``workspace/executeCommand`` request.

        Helper method for :meth:`~LanguageClient.workspace_execute_command_request`
        that reduces the amount of boilerplate required to construct the parameters
        object.

        Parameters
        ----------
        command
           The command name to execute

        args
           Any arguments to pass to the server

        work_done_token
           An optional progress token
        """
        arguments = None if not args else list(args)
        params = ExecuteCommandParams(
            command=command, arguments=arguments, work_done_token=work_done_token
        )
        return await self.workspace_execute_command_request(params)

    async def hover_request(
        self, uri: str, line: int, character: int
    ) -> Optional[Hover]:
        """Make a ``textDocument/hover`` request.

        Helper

        Parameters
        ----------
        uri
           The uri of the document to make the request for.
        line
           The line number to make the request from

        character
           The character column to make the request from
        """

        params = HoverParams(
            text_document=TextDocumentIdentifier(uri=uri),
            position=Position(line=line, character=character),
        )

        return await self.text_document_hover_request(params)

    async def initialize(self, params: InitializeParams) -> InitializeResult:
        """Make an ``initialize`` request to a lanaguage server.

        Helper method for :meth:`LanguageClient.initialize_request` that will
        automatically fill in some of the required fields of ``params`` if they
        are not given.

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
        if params.process_id is None:
            params.process_id = os.getpid()

        response = await self.initialize_request(params)
        self.notify_initialized(InitializedParams())

        return response

    async def implementation_request(
        self, uri: str, line: int, character: int
    ) -> Union[Location, List[Location], List[LocationLink], None]:
        """Make a ``textDocument/implementation`` request to a language server.

        Helper method for :meth:`LanguageClient.text_document_implementation_request`
        that reduces the amount of boilerplate needed to construct the parameters
        object.

        Parameters
        ----------
        uri
           The uri of the document to make the request within.

        line
           The line to make the implementation request from

        character
           The character column to make the implementation request from
        """
        params = ImplementationParams(
            text_document=TextDocumentIdentifier(uri=uri),
            position=Position(line=line, character=character),
        )

        return await self.text_document_implementation_request(params)

    def notify_did_change(
        self,
        uri: str,
        text: str,
        line: Optional[int] = None,
        character: Optional[int] = None,
    ):
        """Send a ``textDocument/didChange`` notification.

        Helper method for :meth:`~LanguageClient.notify_text_document_did_change` that
        automatically sends the correct notification type depending on the given
        arguments. It also does some extra book keeping client side to make sure text
        synchronization is being done in a consistent manner.

        If ``line`` and ``character`` are given, this method will interpret them as the
        position at which the change starts and will automatically compute the end range
        from the lenth of ``text``, before sending a delta update.

        Otherwise it assumes the entire text document is being replaced with ``text``.

        Parameters
        ----------
        uri
           The uri of the document that was changed.

        line
           The line at which the change is being made.

        character
           The character at which the change is being made.

        text
           The text that is being inserted into the document.
        """

        change_event: TextDocumentContentChangeEvent
        version = self.open_documents.get(uri, None)
        if not version:
            raise RuntimeError(f"The document {uri} is not open")

        version += 1
        self.open_documents[uri] = version

        if line is not None and character is not None:
            lines = text.split("\n")
            num_lines = len(lines) - 1
            num_chars = len(lines[-1])

            if num_lines > 0:
                end_char = num_chars
            else:
                end_char = character + num_chars

            change_event = TextDocumentContentChangeEvent_Type1(
                text=text,
                range=Range(
                    start=Position(line=line, character=character),
                    end=Position(line=line + num_lines, character=end_char),
                ),
            )
        else:
            change_event = TextDocumentContentChangeEvent_Type2(text=text)

        params = DidChangeTextDocumentParams(
            text_document=VersionedTextDocumentIdentifier(uri=uri, version=version),
            content_changes=[change_event],
        )
        self.notify_text_document_did_change(params)

    def notify_did_close(self, uri: str):
        """Send a ``textDocument/didClose`` notification.

        Wrapper method for :meth:`~LanguageClient.notify_did_close` that performs some
        extra book keeping client side to help ensure text syncronization is being done
        in a consistent manner.

        Parameters
        ----------
        uri
           The uri of the closed document
        """

        if uri not in self.open_documents:
            raise RuntimeError(f"The document '{uri}' is not open")

        params = DidCloseTextDocumentParams(
            text_document=TextDocumentIdentifier(uri=uri)
        )

        self.notify_text_document_did_close(params)
        self.open_documents.pop(uri)

    def notify_did_open(self, uri: str, language: str, contents: str, version: int = 1):
        """Send a ``textDocument/didOpen`` notification.

        Wrapper method for :meth:`~LanguageClient.notify_text_document_did_open` that
        does some extra book keeping client side to help ensure that text syncronization
        is being done in a consistent manner.

        Parameters
        ----------
        uri
           The uri of the opened document

        language
           The language id of the opened document

        contents
           The contents of the opened document

        version
           The version of the document that was opened, defaults to ``1``
        """

        if uri in self.open_documents:
            raise RuntimeError(f"The document '{uri}' is already open")

        params = DidOpenTextDocumentParams(
            text_document=TextDocumentItem(
                uri=uri, language_id=language, version=version, text=contents
            )
        )

        self.notify_text_document_did_open(params)
        self.open_documents[uri] = version

    def notify_did_save(self, uri: str, text: str):
        """Send a ``textDocument/didSave`` notification

        Wrapper for :meth:`~LanguageClient.notify_did_save` that does some extra book
        keeping client side to help ensure that text syncronization is done in a
        consistent manner.

        Parameters
        ----------
        uri
           The uri of the document that was saved

        text
           The text contained in the saved document
        """

        if uri not in self.open_documents:
            raise RuntimeError(f"The document '{uri}' is not open")

        params = DidSaveTextDocumentParams(
            text_document=TextDocumentIdentifier(uri=uri), text=text
        )

        self.notify_text_document_did_save(params)

    async def notify_did_delete_files(self, *uris: str):
        """Send a ``workspace/didDeleteFiles`` notification

        Helper for :meth:`~LanguageClient.notify_workspace_did_delete_files` the reduces
        the amount of boilerplate required to construct the parameters object.

        Parameters
        ----------
        uris
           The uris of the files that were deleted.
        """

        params = DeleteFilesParams(files=[FileDelete(uri=uri) for uri in uris])
        self.notify_workspace_did_delete_files(params)

    async def shutdown(self) -> None:
        """Shutdown the server under test.

        Helper method that handles sending ``shutdown`` and ``exit`` messages in the
        correct order.

        .. note::

           This method will not attempt to send these messages if a fatal error has
           occurred.

        """
        if self.error is not None:
            return

        await self.shutdown_request(None)
        self.notify_exit(None)

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
        protocol_cls=ClientProtocol,
        converter_factory=default_converter,
        loop=asyncio.new_event_loop(),
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
