from __future__ import annotations

import asyncio
import json
import logging
import os
import pathlib
import sys
import traceback
import typing
import warnings

from lsprotocol import types
from lsprotocol.converters import get_converter
from packaging.version import parse as parse_version
from pygls.exceptions import JsonRpcException
from pygls.exceptions import PyglsError
from pygls.lsp.client import BaseLanguageClient
from pygls.protocol import default_converter

from .checks import LspSpecificationWarning
from .protocol import LanguageClientProtocol

if sys.version_info < (3, 9):
    import importlib_resources as resources
else:
    from importlib import resources  # type: ignore[no-redef]

if typing.TYPE_CHECKING:
    from typing import Any
    from typing import Dict
    from typing import List
    from typing import Optional
    from typing import Type
    from typing import Union


__version__ = "0.4.3"
logger = logging.getLogger(__name__)


class LanguageClient(BaseLanguageClient):
    """Used to drive language servers under test."""

    protocol: LanguageClientProtocol

    def __init__(self, *args, configuration: Optional[Dict[str, Any]] = None, **kwargs):
        if "protocol_cls" not in kwargs:
            kwargs["protocol_cls"] = LanguageClientProtocol

        super().__init__("pytest-lsp-client", __version__, *args, **kwargs)

        self.capabilities: Optional[types.ClientCapabilities] = None
        """The client's capabilities."""

        self.shown_documents: List[types.ShowDocumentParams] = []
        """Holds any received show document requests."""

        self.messages: List[types.ShowMessageParams] = []
        """Holds any received ``window/showMessage`` requests."""

        self.log_messages: List[types.LogMessageParams] = []
        """Holds any received ``window/logMessage`` requests."""

        self.diagnostics: Dict[str, List[types.Diagnostic]] = {}
        """Holds any recieved diagnostics."""

        self.progress_reports: Dict[
            types.ProgressToken, List[types.ProgressParams]
        ] = {}
        """Holds any received progress updates."""

        self.error: Optional[Exception] = None
        """Indicates if the client encountered an error."""

        config = (configuration or {"": {}}).copy()
        if "" not in config:
            config[""] = {}

        self._configuration: Dict[str, Dict[str, Any]] = config
        """Holds ``workspace/configuration`` values."""

        self._setup_log_index = 0
        """Used to keep track of which log messages occurred during startup."""

        self._last_log_index = 0
        """Used to keep track of which log messages correspond with which test case."""

        self._stderr_forwarder: Optional[asyncio.Task] = None
        """A task that forwards the server's stderr to the test process."""

    async def start_io(self, cmd: str, *args, **kwargs):
        await super().start_io(cmd, *args, **kwargs)

        # Forward the server's stderr to this process' stderr
        if self._server and self._server.stderr:
            self._stderr_forwarder = asyncio.create_task(forward_stderr(self._server))

    async def stop(self):
        if self._stderr_forwarder:
            self._stderr_forwarder.cancel()

        return await super().stop()

    async def server_exit(self, server: asyncio.subprocess.Process):
        """Called when the server process exits."""

        if self._stop_event.is_set():
            return

        # TODO: Should the upstream base client be doing this?
        # Cancel any pending futures.
        reason = f"Server process {server.pid} exited with code: {server.returncode}"

        for id_, fut in self.protocol._request_futures.items():
            if not fut.done():
                fut.set_exception(RuntimeError(reason))
                logger.debug("Cancelled pending request '%s': %s", id_, reason)

    def report_server_error(
        self, error: Exception, source: Union[PyglsError, JsonRpcException]
    ):
        """Called when the server does something unexpected, e.g. sending malformed
        JSON."""
        self.error = error
        tb = "".join(traceback.format_exc())

        message = f"{source.__name__}: {error}\n{tb}"  # type: ignore

        loop = asyncio.get_running_loop()
        loop.call_soon(cancel_all_tasks, message)

        if self._stop_event:
            self._stop_event.set()

    def get_configuration(
        self, *, section: Optional[str] = None, scope_uri: Optional[str] = None
    ) -> Optional[Any]:
        """Get a configuration value.

        Parameters
        ----------
        section
           The optional section name to retrieve.
           If ``None`` the top level configuration object for the requested scope will
           be returned

        scope_uri
           The scope at which to set the configuration.
           If ``None``, this will default to the global scope.

        Returns
        -------
        Optional[Any]
           The requested configuration value or ``None`` if not found.
        """
        section = section or ""
        scope = scope_uri or ""

        # Find the longest prefix of ``scope``. The empty string is a prefix of all
        # strings so there will always be at least one match
        candidates = [c for c in self._configuration.keys() if scope.startswith(c)]
        selected = sorted(candidates, key=len, reverse=True)[0]

        if (item := self._configuration.get(selected, None)) is None:
            return None

        if section == "":
            return item

        for segment in section.split("."):
            if not hasattr(item, "get"):
                return None

            if (item := item.get(segment, None)) is None:
                return None

        return item

    def set_configuration(
        self,
        item: Any,
        *,
        section: Optional[str] = None,
        scope_uri: Optional[str] = None,
    ):
        """Set a configuration value.

        Parameters
        ----------
        item
           The value to set

        section
           The optional section name to set.
           If ``None`` the top level configuration object will be overriden with
           ``item``.

        scope_uri
           The scope at which to set the configuration.
           If ``None``, this will default to the global scope.
        """
        section = section or ""
        scope = scope_uri or ""

        if section == "":
            self._configuration[scope] = item
            return

        config = self._configuration.setdefault(scope, {})
        *parents, name = section.split(".")

        for segment in parents:
            config = config.setdefault(segment, {})

        config[name] = item

    async def initialize_session(
        self, params: types.InitializeParams
    ) -> types.InitializeResult:
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
        self.initialized(types.InitializedParams())

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

        await self.shutdown_async(None)

        self.exit(None)
        if self._server:
            await self._server.wait()

    async def wait_for_notification(self, method: str):
        """Block until a notification with the given method is received.

        Parameters
        ----------
        method
           The notification method to wait for, e.g. ``textDocument/publishDiagnostics``
        """
        return await self.protocol.wait_for_notification_async(method)


async def forward_stderr(server: asyncio.subprocess.Process):
    if server.stderr is None:
        return

    # EOF is signalled with an empty bytestring
    while (line := await server.stderr.readline()) != b"":
        sys.stderr.buffer.write(line)


def cancel_all_tasks(message: str):
    """Called to cancel all awaited tasks."""

    for task in asyncio.all_tasks():
        if sys.version_info < (3, 9):
            task.cancel()
        else:
            task.cancel(message)


def make_test_lsp_client() -> LanguageClient:
    """Construct a new test client instance with the handlers needed to capture
    additional responses from the server."""

    client = LanguageClient(
        converter_factory=default_converter,
    )

    @client.feature(types.WORKSPACE_CONFIGURATION)
    def configuration(client: LanguageClient, params: types.ConfigurationParams):
        return [
            client.get_configuration(section=item.section, scope_uri=item.scope_uri)
            for item in params.items
        ]

    @client.feature(types.TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)
    def publish_diagnostics(
        client: LanguageClient, params: types.PublishDiagnosticsParams
    ):
        client.diagnostics[params.uri] = params.diagnostics

    @client.feature(types.WINDOW_WORK_DONE_PROGRESS_CREATE)
    def create_work_done_progress(
        client: LanguageClient, params: types.WorkDoneProgressCreateParams
    ):
        if params.token in client.progress_reports:
            # TODO: Send an error reponse to the client - might require changes
            #       to pygls...
            warnings.warn(
                f"Duplicate progress token: {params.token!r}",
                LspSpecificationWarning,
                stacklevel=2,
            )

        client.progress_reports.setdefault(params.token, [])

    @client.feature(types.PROGRESS)
    def progress(client: LanguageClient, params: types.ProgressParams):
        if params.token not in client.progress_reports:
            warnings.warn(
                f"Unknown progress token: {params.token!r}",
                LspSpecificationWarning,
                stacklevel=2,
            )

        if not params.value:
            return

        if (kind := params.value.get("kind", None)) == "begin":
            type_: Type[Any] = types.WorkDoneProgressBegin
        elif kind == "report":
            type_ = types.WorkDoneProgressReport
        elif kind == "end":
            type_ = types.WorkDoneProgressEnd
        else:
            raise TypeError(f"Unknown progress kind: {kind!r}")

        value = client.protocol._converter.structure(params.value, type_)
        client.progress_reports.setdefault(params.token, []).append(value)

    @client.feature(types.WINDOW_LOG_MESSAGE)
    def log_message(client: LanguageClient, params: types.LogMessageParams):
        client.log_messages.append(params)

        levels = [logger.error, logger.warning, logger.info, logger.debug]
        levels[params.type.value - 1](params.message)

    @client.feature(types.WINDOW_SHOW_MESSAGE)
    def show_message(client: LanguageClient, params):
        client.messages.append(params)

    @client.feature(types.WINDOW_SHOW_DOCUMENT)
    def show_document(
        client: LanguageClient, params: types.ShowDocumentParams
    ) -> types.ShowDocumentResult:
        client.shown_documents.append(params)
        return types.ShowDocumentResult(success=True)

    return client


def client_capabilities(client_spec: str) -> types.ClientCapabilities:
    """Find the capabilities that correspond to the given client spec.

    This function supports the following syntax

    ``client-name`` or ``client-name@latest``
       Return the capabilities of the latest version of ``client-name``

    ``client-name@v2``
       Return the latest release of the ``v2`` of ``client-name``

    ``client-name@v2.3.1``
       Return exactly ``v2.3.1`` of ``client-name``

    Parameters
    ----------
    client_spec
       The string describing the client to load the corresponding
       capabilities for.

    Raises
    ------
    ValueError
       If the requested client's capabilities could not be found

    Returns
    -------
    ClientCapabilities
       The requested client capabilities
    """

    candidates: Dict[str, pathlib.Path] = {}

    client_spec = client_spec.replace("-", "_")
    target_version = "latest"

    if "@" in client_spec:
        client_spec, target_version = client_spec.split("@")
        if target_version.startswith("v"):
            target_version = target_version[1:]

    for resource in resources.files("pytest_lsp.clients").iterdir():
        filename = typing.cast(pathlib.Path, resource)

        # Skip the README or any other files that we don't care about.
        if filename.suffix != ".json":
            continue

        name, version = filename.stem.split("_v")
        if name == client_spec:
            if version.startswith(target_version) or target_version == "latest":
                candidates[version] = filename

    if len(candidates) == 0:
        raise ValueError(
            f"Could not find capabilities for '{client_spec}@{target_version}'"
        )

    # Out of the available candidates, choose the latest version
    selected_version = sorted(candidates.keys(), key=parse_version, reverse=True)[0]
    filename = candidates[selected_version]

    converter = get_converter()
    capabilities = json.loads(filename.read_text())

    params = converter.structure(capabilities, types.InitializeParams)
    logger.info(
        "Selected %s v%s",
        params.client_info.name,  # type: ignore[union-attr]
        params.client_info.version,  # type: ignore[union-attr]
    )

    return params.capabilities
