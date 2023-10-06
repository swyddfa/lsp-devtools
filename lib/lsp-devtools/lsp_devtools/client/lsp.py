import importlib.metadata
import json

from pygls.lsp.client import BaseLanguageClient
from pygls.protocol import LanguageServerProtocol

from lsp_devtools.agent import logger
from lsp_devtools.database import Database

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
