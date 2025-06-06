from __future__ import annotations

import asyncio
import logging
import typing

from lsp_devtools.agent.agent import Header
from lsp_devtools.database import Database

if typing.TYPE_CHECKING:
    from collections.abc import Awaitable
    from typing import Any
    from typing import Callable

    MessageParser = Callable[[asyncio.StreamReader, MessageHandler], Awaitable[Any]]

logger = logging.getLogger(__name__)


async def raw_parser(reader: asyncio.StreamReader, handler):
    """The simplest parser, it only passes on the bytes it receives over the wire."""

    while True:
        try:
            logger.debug("Reading %r header bytes...", Header.size)
            bs = await reader.readexactly(Header.size)
            logger.debug("got: %r", bs)
            source, length = Header.unpack(bs)

            logger.debug("Reading %r payload bytes...", length)
            data = await reader.readexactly(length)
            logger.debug("got: %r", data)
        except asyncio.IncompleteReadError:
            break

        except Exception:
            logger.exception("Unable to parse message")
            continue

        try:
            logger.debug("calling handler")
            handler(data, source)
        except Exception:
            logger.exception("Unable to handle message")


class AgentServer:
    """A server that accepts connections from agents allowing them to send their
    collected messages.

    """

    def __init__(
        self,
        logger: logging.Logger | None = None,
        parser: MessageParser | None = None,
        handler: MessageHandler | None = None,
    ):
        self.logger = logger or logging.getLogger(__name__)
        self.parser = parser or raw_parser
        self.handler = handler
        self.db: Database | None = None

        self._client_buffer: list[str] = []
        self._server_buffer: list[str] = []
        self._tcp_server: asyncio.Task | None = None

    async def start_tcp(self, host: str, port: int) -> None:  # type: ignore[override]
        """Start a TCP server to listen for connections."""

        async def handle_client(
            reader: asyncio.StreamReader, writer: asyncio.StreamWriter
        ):
            """Handle connections from ``AgentClient`` instances"""
            logger.debug("Connected to client.")
            try:
                await self.parser(reader, self.handler)
            except asyncio.CancelledError:
                pass
            finally:
                writer.close()
                await writer.wait_closed()

            logger.debug("Connection closed.")
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
