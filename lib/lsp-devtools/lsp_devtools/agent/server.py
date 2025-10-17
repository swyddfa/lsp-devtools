from __future__ import annotations

import asyncio
import inspect
import logging
import typing

from lsp_devtools.agent.agent import MessageHeader
from lsp_devtools.agent.agent import MessageSource

if typing.TYPE_CHECKING:
    from collections.abc import Awaitable
    from collections.abc import Callable
    from typing import Any
    from typing import Protocol

    class MessageHandler(Protocol):
        """Describes the shape of a message handler."""

        def feed(self, data: bytes, source: MessageSource) -> Awaitable[None] | None:
            """Pass bytes into the handler."""

        def stop(self) -> Awaitable[None] | None:
            """Called when the application stops"""

    MessageParser = Callable[[asyncio.StreamReader, MessageHandler], Awaitable[Any]]

logger = logging.getLogger(__name__)


async def raw_parser(reader: asyncio.StreamReader, handler):
    """The simplest parser, it only passes on the bytes it receives over the wire."""

    while True:
        try:
            bs = await reader.readexactly(MessageHeader.size)
            source, length = MessageHeader.unpack(bs)
            data = await reader.readexactly(length)
        except asyncio.IncompleteReadError:
            break

        except Exception:
            logger.exception("Unable to parse message")
            continue

        try:
            handler(data, source)
        except Exception:
            logger.exception("Unable to handle message")


class AgentServer:
    """A server that accepts connections from agents allowing them to send their
    collected messages.

    Parameters
    ----------
    handlers
       A dictionary mapping message sources to corresponding message handler instances

    logger
       Logger instance to use, if not given a default logger derived from the moddule
       name will be used insteaa.

    persistent
       If ``True``, (the default) the server will keep running after the connection
       drops. Otherwise the server will exit after the first connection closes.
    """

    def __init__(
        self,
        handlers: dict[MessageSource, MessageHandler] | None = None,
        logger: logging.Logger | None = None,
        persistent: bool = True,
    ):
        self.logger: logging.Logger = logger or logging.getLogger(__name__)
        self.handlers: dict[MessageSource, MessageHandler] = handlers or {}
        self.persistent = persistent

        self._client_buffer: list[str] = []
        self._server_buffer: list[str] = []
        self._tasks: set[asyncio.Task[Any]] = set()
        self._tcp_server: asyncio.Task[Any] | None = None

    async def run_connection(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        """Handle connections from ``AgentClient`` instances"""
        self.logger.debug("Connected to client.")
        try:
            while True:
                try:
                    bs = await reader.readexactly(MessageHeader.size)
                    source, length = MessageHeader.unpack(bs)
                    data = await reader.readexactly(length)
                except asyncio.IncompleteReadError:
                    break

                except Exception:
                    self.logger.exception("Unable to parse message")
                    continue

                try:
                    if (handler := self.handlers.get(source)) is None:
                        continue

                    if inspect.isawaitable(res := handler.feed(data, source)):
                        task = asyncio.ensure_future(res)
                        task.add_done_callback(self._tasks.discard)
                        self._tasks.add(task)

                except Exception:
                    self.logger.exception("Unable to handle message")

        except asyncio.CancelledError:
            pass
        finally:
            writer.close()
            await writer.wait_closed()

        self.logger.debug("Connection closed.")

        if not self.persistent:
            self.stop()

    async def start_tcp(self, host: str, port: int) -> None:  # type: ignore[override]
        """Start a TCP server to listen for connections."""
        server = await asyncio.start_server(self.run_connection, host, port)
        async with server:
            self._tcp_server = asyncio.create_task(server.serve_forever())
            await self._tcp_server

    def stop(self):
        for handler in self.handlers.values():
            try:
                if inspect.isawaitable(res := handler.stop()):
                    task = asyncio.ensure_future(res)
                    task.add_done_callback(self._tasks.discard)
                    self._tasks.add(task)
            except Exception:
                self.logger.exception("Error stopping handler")

        if self._tcp_server is not None:
            self._tcp_server.cancel()
