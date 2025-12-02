from __future__ import annotations

import asyncio
import typing

from pygls.lsp.client import LanguageClient as BaseLanguageClient

from lsp_devtools.agent.agent import MessageSource
from lsp_devtools.handlers.jsonrpc import JsonRPCHandler

if typing.TYPE_CHECKING:
    from collections.abc import Awaitable

    from pygls.protocol import JsonRPCProtocol

    from lsp_devtools.handlers.jsonrpc import JsonRPCMessage


class MessageWriter:
    """A writer compatible with pygls' AsyncWriter interface."""

    def __init__(self, handler: JsonRPCHandler, dest: asyncio.StreamWriter):
        self.handler = handler
        self.dest = dest

    def close(self) -> Awaitable[None]:
        self.dest.close()
        return self.dest.wait_closed()

    def write(self, data: bytes) -> Awaitable[None]:
        self.handler.feed(data, MessageSource.CLIENT)
        self.dest.write(data)
        return self.dest.drain()


class MessageHandler(JsonRPCHandler):
    """A message handler that forwards messages to both pygls and the given message handler."""

    def __init__(self, handler: JsonRPCHandler, protocol: JsonRPCProtocol):
        super().__init__()
        self.handler: JsonRPCHandler = handler
        self.protocol: JsonRPCProtocol = protocol

    def handle(self, message: JsonRPCMessage):
        self.handler.handle(message)

        typed_message = self.protocol.structure_message(message.body)
        self.protocol.handle_message(typed_message)


class LanguageClient(BaseLanguageClient):
    """A modified version of pygls' built-in language client that integrates with our
    message handling infrastructure."""

    def __init__(self, handler: JsonRPCHandler, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.handler: JsonRPCHandler = handler

    async def start_io(self, cmd: str, *args, **kwargs):
        """Start the given server and communicate with it over stdio.

        This overrides the version of this method upstream so that bytes are pushed
        through the given JsonRPCHandler.
        """

        # logger.debug("Starting server process: %s", " ".join([cmd, *args]))
        server = await asyncio.create_subprocess_exec(
            cmd,
            *args,
            stdout=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            **kwargs,
        )

        # Keep mypy happy
        if server.stdout is None:
            raise RuntimeError("Server process is missing a stdout stream")

        # Keep mypy happy
        if server.stdin is None:
            raise RuntimeError("Server process is missing a stdin stream")

        self.protocol.set_writer(MessageWriter(self.handler, server.stdin))
        connection = asyncio.create_task(
            self.connect_streams(
                source=server.stdout,
                dest=MessageHandler(self.handler, self.protocol),
                origin=MessageSource.SERVER,
            )
        )
        notify_exit = asyncio.create_task(self._server_exit())

        self._server = server
        self._async_tasks.extend([connection, notify_exit])

    async def connect_streams(
        self, source: asyncio.StreamReader, dest: MessageHandler, origin: MessageSource
    ):
        """Forward bytes from the source to the destination, while simultaneously
        passing them to the handler function"""

        while (data := await source.read(1024)) != b"":
            dest.feed(data, origin)
