from __future__ import annotations

import asyncio
import logging
import traceback
import typing

from pygls.protocol import default_converter
from pygls.server import Server

from lsp_devtools.agent.agent import aio_readline
from lsp_devtools.agent.protocol import AgentProtocol
from lsp_devtools.database import Database

if typing.TYPE_CHECKING:
    from typing import Any
    from typing import List
    from typing import Optional

    from lsp_devtools.agent.agent import MessageHandler


class AgentServer(Server):
    """A pygls server that accepts connections from agents allowing them to send their
    collected messages."""

    lsp: AgentProtocol

    def __init__(
        self,
        *args,
        logger: Optional[logging.Logger] = None,
        handler: Optional[MessageHandler] = None,
        **kwargs,
    ):
        if "protocol_cls" not in kwargs:
            kwargs["protocol_cls"] = AgentProtocol

        if "converter_factory" not in kwargs:
            kwargs["converter_factory"] = default_converter

        super().__init__(*args, **kwargs)

        self.logger = logger or logging.getLogger(__name__)
        self.handler = handler or self.lsp.data_received
        self.db: Optional[Database] = None

        self._client_buffer: List[str] = []
        self._server_buffer: List[str] = []
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
                await aio_readline(reader, self.handler)
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
