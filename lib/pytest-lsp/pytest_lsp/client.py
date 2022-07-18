import asyncio
import logging
from concurrent.futures import Future
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

from pygls.exceptions import JsonRpcMethodNotFound
from pygls.lsp.methods import *
from pygls.lsp.types import *
from pygls.protocol import LanguageServerProtocol
from pygls.server import LanguageServer

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

    def wait_for_notification(self, method, callback=None):

        future = Future()
        if callback:

            def wrapper(future: Future):
                result = future.result()
                callback(result)

            future.add_done_callback(wrapper)

        self._notification_futures[method] = future
        return future

    def wait_for_notification_async(self, method):
        future = self.wait_for_notification(method)
        return asyncio.wrap_future(future)


class Client(LanguageServer):
    """Used to drive language servers under test."""

    def __init__(
        self, capabilities: ClientCapabilities, root_uri: str, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)

        self.capabilities: ClientCapabilities = capabilities
        """The client's capabilities."""

        self.root_uri: str = root_uri
        """The root uri of the client's workspace."""

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

        self._setup_log_index = 0
        """Used to keep track of which log messages occurred during startup."""

        self._last_log_index = 0
        """Used to keep track of which log messages correspond with which test case."""

    async def completion_request(
        self,
        uri: str,
        line: int,
        character: int,
    ) -> Optional[Union[CompletionList, List[CompletionItem]]]:
        """Send a ``textDocument/completion`` request.

        Parameters
        ----------
        uri
           The uri of the document to make the completion request from
        line
           The line number to make the completion request from
        character
           The character column to make the completion request from.

        Return
        ------
        Optional[Union[CompletionList, List[CompletionItem]]]
           Either a list of CompletionItem, a CompletionList or None
           based on the response of the language server, corresponding
           to 'CompletionItem[] | CompletionList | null'.
        """

        response = await self.lsp.send_request_async(
            COMPLETION,
            CompletionParams(
                text_document=TextDocumentIdentifier(uri=uri),
                position=Position(line=line, character=character),
            ),
        )

        if isinstance(response, dict):
            return CompletionList(**response)
        elif isinstance(response, list):
            return [CompletionItem(**item) for item in response]
        else:
            return None

    async def completion_resolve_request(self, item: CompletionItem) -> CompletionItem:
        """Make a ``completionItem/resolve`` request to a language server.

        Parameters
        ----------
        item
           The ``CompletionItem`` to be resolved.

        Return
        ------
        CompletionItem
           The resolved completion item.
        """

        response = await self.lsp.send_request_async(COMPLETION_ITEM_RESOLVE, item)
        return CompletionItem(**response)

    async def definition_request(
        self, uri: str, position: Position
    ) -> Optional[Union[Location, List[Location], List[LocationLink]]]:
        """Make a ``textDocument/definition`` request to a language server.

        Parameters
        ----------
        uri
           The uri of the document to make the request within.
        position
           The position of the definition request.

        Return
        ------
        Optional[Union[Location, List[Location], List[LocationLink]]]
           Either a Location, list of Location, a list of LocationLink
           or None based on the response of the language server,
           corresponding to 'Location | Location[] | LocationLink[] | null'.
        """
        response = await self.lsp.send_request_async(
            DEFINITION,
            DefinitionParams(
                text_document=TextDocumentIdentifier(uri=uri), position=position
            ),
        )

        if isinstance(response, list):
            return [
                LocationLink(**obj) if "targetUri" in obj else Location(**obj)
                for obj in response
            ]
        elif isinstance(response, dict):
            return Location(**response)
        else:
            return None

    async def document_link_request(self, uri: str) -> Optional[List[DocumentLink]]:
        """Make a ``textDocument/documentLink`` request

        Parameters
        ----------
        uri
           The uri of the document to make the request for.

        Return
        ------
        Optional[List[DocumentLink]]
           Either a list of DocumentLink or None based on the response of the
           language server, corresponding to 'DocumentLink[] | null'.
        """

        response = await self.lsp.send_request_async(
            DOCUMENT_LINK,
            DocumentLinkParams(text_document=TextDocumentIdentifier(uri=uri)),
        )

        if response:
            return [DocumentLink(**obj) for obj in response]
        else:
            return None

    async def document_symbols_request(
        self, uri: str
    ) -> Optional[Union[List[DocumentSymbol], List[SymbolInformation]]]:
        """Make a ``textDocument/documentSymbol`` request

        Parameters
        ----------
        uri
           The uri of the document to make the request for.

        Return
        ------
        Optional[Union[List[DocumentSymbol], List[SymbolInformation]]]
           Either a list of DocumentSymbol, a list of SymbolInformation
           or None based on the response of the language server, corresponding
           to 'DocumentSymbol[] | SymbolInformation[] | null'.
        """

        response = await self.lsp.send_request_async(
            DOCUMENT_SYMBOL,
            DocumentSymbolParams(text_document=TextDocumentIdentifier(uri=uri)),
        )

        if response:
            return [
                DocumentSymbol(**obj) if "range" in obj else SymbolInformation(**obj)
                for obj in response
            ]
        else:
            return None

    async def hover_request(self, uri: str, position: Position) -> Optional[Hover]:
        """Make a ``textDocument/hover`` request.

        Parameters
        ----------
        uri
           The uri of the document to make the request for.
        position
           The position of the hover request

        Return
        ------
        Optional[Hover]
           A Hover or None based on the response of the language server,
           corresponding to 'Hover | null'.
        """

        response = await self.lsp.send_request_async(
            HOVER,
            HoverParams(
                text_document=TextDocumentIdentifier(uri=uri), position=position
            ),
        )

        if response:
            return Hover(**response)
        else:
            return None

    async def implementation_request(
        self, uri: str, position: Position
    ) -> Optional[Union[Location, List[Location], List[LocationLink]]]:
        """Make a ``textDocument/implementation`` request to a language server.

        Parameters
        ----------
        uri
           The uri of the document to make the request within.
        position
           The position of the implementation request.

        Return
        ------
        Optional[Union[Location, List[Location], List[LocationLink]]]
           Either a Location, list of Location, a list of LocationLink
           or None based on the response of the language server,
           corresponding to 'Location | Location[] | LocationLink[] | null'.
        """
        response = await self.lsp.send_request_async(
            IMPLEMENTATION,
            ImplementationParams(
                text_document=TextDocumentIdentifier(uri=uri), position=position
            ),
        )

        if isinstance(response, list):
            return [
                LocationLink(**obj) if "targetUri" in obj else Location(**obj)
                for obj in response
            ]
        elif isinstance(response, dict):
            return Location(**response)
        else:
            return None

    async def execute_command_request(self, command: str, *args: Any):
        return await self.lsp.send_request_async(
            WORKSPACE_EXECUTE_COMMAND,
            ExecuteCommandParams(command=command, arguments=list(args)),
        )

    def notify_did_change(
        self,
        uri: str,
        text: str,
        line: Optional[int] = None,
        character: Optional[int] = None,
    ):
        """Notify the server that a text document was changed.

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

            change_event = TextDocumentContentChangeEvent(
                text=text,
                range=Range(
                    start=Position(line=line, character=character),
                    end=Position(line=line + num_lines, character=end_char),
                ),
            )
        else:
            change_event = TextDocumentContentChangeTextEvent(text=text)

        self.lsp.notify(
            TEXT_DOCUMENT_DID_CHANGE,
            DidChangeTextDocumentParams(
                text_document=VersionedTextDocumentIdentifier(uri=uri, version=version),
                content_changes=[change_event],
            ),
        )

    def notify_did_close(self, uri: str):
        """Notify the server that a text document was closed.

        Parameters
        ----------
        uri
           The uri of the closed document
        """

        if uri not in self.open_documents:
            raise RuntimeError(f"The document '{uri}' is not open")

        self.lsp.notify(
            TEXT_DOCUMENT_DID_CLOSE,
            DidCloseTextDocumentParams(text_document=TextDocumentIdentifier(uri=uri)),
        )

        del self.open_documents[uri]

    def notify_did_open(
        self, uri: str, language: str, contents: str, version: NumType = 1
    ):
        """Notify the server that a text document was opened.

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

        self.lsp.notify(
            TEXT_DOCUMENT_DID_OPEN,
            DidOpenTextDocumentParams(
                text_document=TextDocumentItem(
                    uri=uri, language_id=language, version=version, text=contents
                )
            ),
        )

        self.open_documents[uri] = version

    def notify_did_save(self, uri: str, text: str):
        """Notify the server that a document was saved.

        Parameters
        ----------
        uri
           The uri of the document that was saved

        text
           The text contained in the saved document
        """

        if uri not in self.open_documents:
            raise RuntimeError(f"The document '{uri}' is not open")

        self.lsp.notify(
            TEXT_DOCUMENT_DID_SAVE,
            DidSaveTextDocumentParams(
                text_document=TextDocumentIdentifier(uri=uri), text=text
            ),
        )

    async def notify_did_delete_files(self, *uris: str):
        """Notify the server that files were deleted.

        Parameters
        ----------
        uris
           The uris of the files that were deleted.
        """

        self.lsp.notify(
            WORKSPACE_DID_DELETE_FILES,
            DeleteFilesParams(files=[FileDelete(uri=uri) for uri in uris]),
        )

    async def send_request(self, *args, **kwargs):
        """Generic send request method."""
        return await self.lsp.send_request_async(*args, **kwargs)

    async def wait_for_notification(self, *args, **kwargs):
        return await self.lsp.wait_for_notification_async(*args, **kwargs)


def make_test_client(capabilities: ClientCapabilities, root_uri: str) -> Client:
    """Construct a new test client instance with the handlers needed to capture additional
    responses from the server."""

    client = Client(
        capabilities,
        root_uri,
        protocol_cls=ClientProtocol,
        loop=asyncio.new_event_loop(),
    )

    @client.feature(TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)
    def publish_diagnostics(client: Client, params: PublishDiagnosticsParams):
        client.diagnostics[params.uri] = [
            Diagnostic(**object_to_dict(obj)) for obj in params.diagnostics
        ]

    @client.feature(WINDOW_LOG_MESSAGE)
    def log_message(client: Client, params):
        log = LogMessageParams(**object_to_dict(params))
        client.log_messages.append(log)

        levels = [logger.error, logger.warning, logger.info, logger.debug]
        levels[log.type - 1](log.message)

    @client.feature(WINDOW_SHOW_MESSAGE)
    def show_message(client: Client, params):
        client.messages.append(params)

    @client.feature(WINDOW_SHOW_DOCUMENT)
    def show_document(client: Client, params: ShowDocumentParams):
        client.shown_documents.append(params)

    return client


def object_to_dict(obj) -> Dict[str, Any]:
    """Convert a pygls.protocol.Object to a dictionary."""

    if hasattr(obj, "_asdict"):
        return {k: object_to_dict(v) for k, v in obj._asdict().items()}

    return obj
