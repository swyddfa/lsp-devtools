import asyncio
import json
import logging
import re
import threading
import traceback
from typing import Any
from typing import List
from typing import Optional

from pygls.client import aio_readline
from pygls.protocol import default_converter
from pygls.server import Server

from lsp_devtools.agent.protocol import AgentProtocol
from lsp_devtools.agent.protocol import MessageText
from lsp_devtools.database import Database


class AgentServer(Server):
    """A pygls server that accepts connections from agents allowing them to send their
    collected messages."""

    lsp: AgentProtocol

    def __init__(self, *args, logger: Optional[logging.Logger] = None, **kwargs):
        if "protocol_cls" not in kwargs:
            kwargs["protocol_cls"] = AgentProtocol

        if "converter_factory" not in kwargs:
            kwargs["converter_factory"] = default_converter

        super().__init__(*args, **kwargs)

        self.logger = logger or logging.getLogger(__name__)
        self.db: Optional[Database] = None

        self._client_buffer: List[str] = []
        self._server_buffer: List[str] = []
        self._stop_event = threading.Event()
        self._tcp_server: Optional[asyncio.Task] = None

    def _report_server_error(self, exc: Exception, source):
        """Report internal server errors."""
        tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        self.logger.error("%s: %s", type(exc).__name__, exc)
        self.logger.debug("%s", tb)

    def feature(self, feature_name: str, options: Optional[Any] = None):
        return self.lsp.fm.feature(feature_name, options)

    async def start_tcp(self, host: str, port: int) -> None:  # type: ignore[override]
        async def handle_client(reader, writer):
            self.lsp.connection_made(writer)

            try:
                await aio_readline(self._stop_event, reader, self.lsp.data_received)
            except asyncio.CancelledError:
                pass
            finally:
                writer.close()
                await writer.wait_closed()

            # Uncomment if we ever need to introduce a mode where the server stops
            # automatically once a session ends.
            #
            # self.stop()

        server = await asyncio.start_server(handle_client, host, port)
        async with server:
            self._tcp_server = asyncio.create_task(server.serve_forever())
            await self._tcp_server

    def stop(self):
        if self._tcp_server is not None:
            self._tcp_server.cancel()


MESSAGE_PATTERN = re.compile(
    r"^(?:[^\r\n]+\r\n)*"
    + r"Content-Length: (?P<length>\d+)\r\n"
    + r"(?:[^\r\n]+\r\n)*\r\n"
    + r"(?P<body>{.*)",
    re.DOTALL,
)


def parse_rpc_message(ls: AgentServer, message: MessageText, callback):
    """Parse json-rpc messages coming from the agent.

    Originally adatped from the ``data_received`` method on pygls' ``JsonRPCProtocol``
    class.
    """
    data = message.text
    message_buf = ls._client_buffer if message.source == "client" else ls._server_buffer

    while len(data):
        # Append the incoming chunk to the message buffer
        message_buf.append(data)

        # Look for the body of the message
        msg = "".join(message_buf)
        found = MESSAGE_PATTERN.fullmatch(msg)

        body = found.group("body") if found else ""
        length = int(found.group("length")) if found else 1

        if len(body) < length:
            # Message is incomplete; bail until more data arrives
            return

        # Message is complete;
        # extract the body and any remaining data,
        # and reset the buffer for the next message
        body, data = body[:length], body[length:]
        message_buf.clear()

        callback(json.loads(body))
