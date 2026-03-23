from __future__ import annotations

import asyncio
import enum
import logging
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


class ClientState(enum.Enum):
    """The set of possible states the server may be in."""

    Starting = enum.auto()
    """The server is starting."""

    Restarting = enum.auto()
    """The server is restarting."""

    Running = enum.auto()
    """The server is running normally."""

    Errored = enum.auto()
    """The server has enountered some unrecoverable error and should not be used."""

    Exited = enum.auto()
    """The server is no longer running."""


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
        logger: logging.Logger | None = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.logger = logger or logging.getLogger(__name__)
        self.state: ClientState | None = None
        self.message_handler: JsonRPCHandler = message_handler

    async def start_io(self, cmd: str, *args, **kwargs):
        """Start the given server and communicate with it over stdio.

        This overrides the version of this method upstream so that bytes are pushed
        through the given JsonRPCHandler.
        """

        try:
            await self._start_io(cmd, *args, **kwargs)
            self.state = ClientState.Running
        except Exception as exc:
            self.logger.error("Unable to start server: %s", exc)
            self.state = ClientState.Errored

    async def _start_io(self, cmd: str, *args, **kwargs):
        self.state = ClientState.Starting

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

        self.logger.debug("Started server [%s]: %s %s", server.pid, cmd, " ".join(args))
        self.protocol.set_writer(MessageWriter(self.message_handler, server.stdin))

        self._async_tasks.append(
            asyncio.create_task(
                self.connect_streams(
                    source=server.stdout,
                    dest=MessageHandler(self.message_handler, self.protocol),
                    origin=MessageSource.SERVER,
                ),
                name="server-connection",
            )
        )
        self._async_tasks.append(
            asyncio.create_task(self._server_exit(), name="exit-notifier"),
        )
        self._async_tasks.append(
            asyncio.create_task(
                forward_stderr(server.stderr, self.logger), name="stderr-stream"
            )
        )

        self._server = server

    async def connect_streams(
        self, source: asyncio.StreamReader, dest: MessageHandler, origin: MessageSource
    ):
        """Forward bytes from the source to the destination, while simultaneously
        passing them to the handler function"""

        while (data := await source.read(1024)) != b"":
            dest.feed(data, origin)

    async def server_exit(self, server: asyncio.subprocess.Process):
        """Called when the server process exits."""
        if server.returncode != 0:
            self.logger.error("Server process exited with code: %s", server.returncode)
            self.state = ClientState.Errored
        else:
            self.logger.debug("Server process exited with code: %s", server.returncode)
            self.state = ClientState.Exited


async def forward_stderr(stderr: asyncio.StreamReader, logger: logging.Logger):
    """Forward stderr output onto the given handler."""

    while (data := await stderr.readline()) != b"":
        logger.info(data.decode("utf-8"))
