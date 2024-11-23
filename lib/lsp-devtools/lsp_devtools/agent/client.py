from __future__ import annotations

import asyncio
import inspect
import typing

import stamina
from pygls.client import JsonRPCClient
from pygls.protocol import default_converter

from lsp_devtools.agent.protocol import AgentProtocol

if typing.TYPE_CHECKING:
    from typing import Any


class AgentClient(JsonRPCClient):
    """Client for connecting to an AgentServer instance."""

    protocol: AgentProtocol

    def __init__(self):
        super().__init__(
            protocol_cls=AgentProtocol, converter_factory=default_converter
        )
        self.connected = False
        self._buffer: list[bytes] = []
        self._tasks: set[asyncio.Task[Any]] = set()

    def _report_server_error(self, error, source):
        # Bail on error
        # TODO: Report the actual error somehow
        self._stop_event.set()

    def feature(self, feature_name: str, options: Any | None = None):
        return self.protocol.fm.feature(feature_name, options)

    async def start_tcp(self, host: str, port: int):
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
                await super().start_tcp(host, port)
                self.connected = True

    def forward_message(self, message: bytes):
        """Forward the given message to the server instance."""

        if not self.connected or self.protocol.writer is None:
            self._buffer.append(message)
            return

        # Send any buffered messages
        while len(self._buffer) > 0:
            res = self.protocol.writer.write(self._buffer.pop(0))
            if inspect.isawaitable(res):
                task = asyncio.ensure_future(res)
                task.add_done_callback(self._tasks.discard)
                self._tasks.add(task)

        res = self.protocol.writer.write(message)
        if inspect.isawaitable(res):
            task = asyncio.ensure_future(res)
            task.add_done_callback(self._tasks.discard)
            self._tasks.add(task)
