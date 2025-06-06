from __future__ import annotations

import asyncio
import inspect
import logging
import typing

import stamina

if typing.TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)


class AgentClient:
    """Client for connecting to an AgentServer instance."""

    def __init__(self):
        self.connected = False
        self._buffer: list[bytes] = []
        self._tasks: set[asyncio.Task[Any]] = set()

        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None

    async def start_tcp(self, host: str, port: int):
        """Create a TCP connection to an ``AgentServer`` instance"""
        # The user might not have started the server app immediately and since the
        # agent will live as long as the wrapper language server we may as well
        # try indefinitely.
        retries = stamina.retry_context(
            on=OSError,
            attempts=None,
            timeout=None,
            wait_initial=1,
            wait_max=60,
        )
        async for attempt in retries:
            with attempt:
                logger.debug("connecting...")
                self.reader, self.writer = await asyncio.open_connection(host, port)
                self.connected = True
                logger.debug("connected.")

    def forward_message(self, message: bytes):
        """Forward the given message to the server instance."""

        if not self.connected or self.writer is None:
            self._buffer.append(message)
            return

        # Send any buffered messages
        while len(self._buffer) > 0:
            res = self.writer.write(self._buffer.pop(0))
            if inspect.isawaitable(res):
                task = asyncio.ensure_future(res)
                task.add_done_callback(self._tasks.discard)
                self._tasks.add(task)

        logger.debug("sending message: %r", message)
        res = self.writer.write(message)
        if inspect.isawaitable(res):
            task = asyncio.ensure_future(res)
            task.add_done_callback(self._tasks.discard)
            self._tasks.add(task)
