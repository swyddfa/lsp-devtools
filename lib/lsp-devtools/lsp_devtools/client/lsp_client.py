from __future__ import annotations

import asyncio
import inspect
import typing

from pygls.lsp.client import LanguageClient as BaseLanguageClient

from lsp_devtools.agent.agent import MessageSource
from lsp_devtools.handlers.jsonrpc import JsonRPCHandler

if typing.TYPE_CHECKING:
    from collections.abc import Awaitable
    from collections.abc import Callable

    from pygls.protocol import JsonRPCProtocol

    from lsp_devtools.handlers.jsonrpc import JsonRPCMessage

    StderrHandler = Callable[[bytes], None | Awaitable[None]]


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

    def __init__(
        self,
        message_handler: JsonRPCHandler,
        stderr_handler: StderrHandler | None = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.message_handler: JsonRPCHandler = message_handler
        self.stderr_handler: StderrHandler | None = stderr_handler

    async def start_io(self, cmd: str, *args, **kwargs):
        """Start the given server and communicate with it over stdio.

        This overrides the version of this method upstream so that bytes are pushed
        through the given JsonRPCHandler.
        """

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

        # Keep mypy happy
        if server.stderr is None:
            raise RuntimeError("Server process is missing a stderr stream")

        self.protocol.set_writer(MessageWriter(self.message_handler, server.stdin))
        connection = asyncio.create_task(
            self.connect_streams(
                source=server.stdout,
                dest=MessageHandler(self.message_handler, self.protocol),
                origin=MessageSource.SERVER,
            )
        )
        notify_exit = asyncio.create_task(self._server_exit())

        self._server = server
        self._async_tasks.extend([connection, notify_exit])

        if self.stderr_handler is not None:
            self._async_tasks.append(
                asyncio.create_task(forward_stderr(server.stderr, self.stderr_handler))
            )

    async def connect_streams(
        self, source: asyncio.StreamReader, dest: MessageHandler, origin: MessageSource
    ):
        """Forward bytes from the source to the destination, while simultaneously
        passing them to the handler function"""

        while (data := await source.read(1024)) != b"":
            dest.feed(data, origin)


async def forward_stderr(stderr: asyncio.StreamReader, handler: StderrHandler):
    """Forward stderr output onto the given handler."""

    while (data := await stderr.readline()) != b"":
        if inspect.isawaitable(res := handler(data)):
            await res
