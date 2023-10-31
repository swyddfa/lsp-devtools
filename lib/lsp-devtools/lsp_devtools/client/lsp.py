import importlib.metadata
import json
from typing import Optional

from lsprotocol import types
from pygls.lsp.client import BaseLanguageClient
from pygls.protocol import LanguageServerProtocol

from lsp_devtools.agent import logger

VERSION = importlib.metadata.version("lsp-devtools")


class RecordingLSProtocol(LanguageServerProtocol):
    """A version of the LanguageServerProtocol that also records all the traffic."""

    def __init__(self, server, converter):
        super().__init__(server, converter)

    def _procedure_handler(self, message):
        logger.info(
            "%s",
            json.dumps(message, default=self._serialize_message),
            extra={"source": "server"},
        )
        return super()._procedure_handler(message)

    def _send_data(self, data):
        logger.info(
            "%s",
            json.dumps(data, default=self._serialize_message),
            extra={"source": "client"},
        )
        return super()._send_data(data)


class LanguageClient(BaseLanguageClient):
    """A language client for integrating with a textual text edit."""

    def __init__(self):
        super().__init__("lsp-devtools", VERSION, protocol_cls=RecordingLSProtocol)

        self._server_capabilities: Optional[types.ServerCapabilities] = None

    @property
    def server_capabilities(self) -> types.ServerCapabilities:
        if self._server_capabilities is None:
            raise RuntimeError(
                "sever_capabilities is None - has the server been initialized?"
            )

        return self._server_capabilities

    async def initialize_async(
        self, params: types.InitializeParams
    ) -> types.InitializeResult:
        result = await super().initialize_async(params)
        self._server_capabilities = result.capabilities

        return result
