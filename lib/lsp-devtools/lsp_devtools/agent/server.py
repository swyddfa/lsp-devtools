from __future__ import annotations

import asyncio
import json
import logging
import traceback
import typing

from pygls.protocol import default_converter
from pygls.server import JsonRPCServer

from lsp_devtools.agent.agent import aio_readline
from lsp_devtools.agent.protocol import AgentProtocol
from lsp_devtools.database import Database

if typing.TYPE_CHECKING:
    from typing import Any

    from lsp_devtools.agent.agent import MessageHandler


class AgentServer(JsonRPCServer):
    """A pygls server that accepts connections from agents allowing them to send their
    collected messages."""

    lsp: AgentProtocol

    def __init__(
        self,
        *args,
        logger: logging.Logger | None = None,
        handler: MessageHandler | None = None,
        **kwargs,
    ):
        if "protocol_cls" not in kwargs:
            kwargs["protocol_cls"] = AgentProtocol

        if "converter_factory" not in kwargs:
            kwargs["converter_factory"] = default_converter

        super().__init__(*args, **kwargs)

        self.logger = logger or logging.getLogger(__name__)
        self.handler = handler or self._default_handler
        self.db: Database | None = None

        self._client_buffer: list[str] = []
        self._server_buffer: list[str] = []
        self._tcp_server: asyncio.Task | None = None

    def _default_handler(self, data: bytes):
        message = self.protocol.structure_message(json.loads(data))
        self.protocol.handle_message(message)

    def _report_server_error(self, error: Exception, source):
        """Report internal server errors."""
        tb = "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )
        self.logger.error("%s: %s", type(error).__name__, error)
        self.logger.debug("%s", tb)

    def feature(self, feature_name: str, options: Any | None = None):
        return self.lsp.fm.feature(feature_name, options)

    async def start_tcp(self, host: str, port: int) -> None:  # type: ignore[override]
        async def handle_client(
            reader: asyncio.StreamReader, writer: asyncio.StreamWriter
        ):
            self.protocol.set_writer(writer)

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
