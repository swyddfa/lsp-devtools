from __future__ import annotations

import asyncio
import inspect
import json
import logging
import typing
from collections import defaultdict
from datetime import datetime
from datetime import timezone

import attrs

from lsp_devtools.agent.agent import MessageHeader
from lsp_devtools.agent.agent import MessageSource
from lsp_devtools.database import Database

if typing.TYPE_CHECKING:
    from collections.abc import Awaitable
    from collections.abc import Callable
    from typing import Any
    from typing import Literal
    from typing import Protocol

    JsonRPCMessageType = Literal[
        "request", "response", "result", "error", "notification"
    ]

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
    collected messages."""

    def __init__(
        self,
        handlers: dict[MessageSource, MessageHandler] | None = None,
        logger: logging.Logger | None = None,
    ):
        self.logger: logging.Logger = logger or logging.getLogger(__name__)
        self.handlers: dict[MessageSource, MessageHandler] = handlers or {}
        self.db: Database | None = None

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
        # Uncomment if we ever need to introduce a mode where the server stops
        # automatically once a session ends.
        #
        # self.stop()

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


@attrs.define
class JsonRPCMessage:
    """A Json-RPC message."""

    metadata: dict[str, Any]

    headers: dict[str, str]

    body: dict[str, Any]

    def __getitem__(self, key: str):
        return self.headers[key]

    @property
    def method(self) -> str | None:
        """Return the JSON-RPC method name, if present"""
        return self.body.get("method")

    @property
    def msg_id(self) -> str | int | None:
        """Return the id of the JSON-RPC message, if present"""
        return self.body.get("id")

    @property
    def msg_type(self) -> JsonRPCMessageType:
        """Return the type of JSON-RPC message this represents"""
        if "id" in self.body:
            if "error" in self.body:
                return "error"
            elif "method" in self.body:
                return "request"
            else:
                return "result"
        else:
            return "notification"


@attrs.define
class ParserState:
    buffer: bytearray = attrs.field(factory=bytearray)
    """Bytes that have not yet been parsed"""

    headers: dict[str, str] = attrs.field(factory=dict)
    """Parsed headers"""

    headers_complete: bool = attrs.field(default=False)
    """Flag indicating if all the headers for this message have been parsed."""

    @property
    def content_length(self) -> int:
        """Return the value of the content length header or ``-1`` if it's not defined."""

        if (value := self.headers.get("Content-Length")) is None:
            return -1

        return int(value)


class JsonRPCHandler:
    """A message handler for Json-RPC messages"""

    def __init__(self):
        self._parsers: dict[MessageSource, ParserState] = defaultdict(ParserState)
        self._tasks: set[asyncio.Task[Any]] = set()

    def handle(self, message: JsonRPCMessage):
        """Handle the messages."""
        raise NotImplementedError()

    def feed(self, data: bytes, source: MessageSource):
        """Parse a JSON-RPC message from the given set of bytes."""

        SEP = b"\r\n"

        state = self._parsers[source]
        state.buffer += data

        # We want to make sure that we consume as many bytes as possible - we never
        # know how long it will be before we receive more and we don't want complete
        # messages to be stuck in the buffer...
        #
        # So we will keep running that parser as long as the buffer continues to shrink
        previous_length = len(state.buffer) + 1
        while len(state.buffer) < previous_length:
            previous_length = len(state.buffer)

            if not state.headers_complete:
                if (idx := state.buffer.find(SEP)) == -1:
                    return

                line, state.buffer = state.buffer[:idx], state.buffer[idx + len(SEP) :]
                if line == b"":
                    state.headers_complete = True
                    continue

                elif (idx := line.find(b":")) == -1:
                    raise ValueError(f"Invalid message header: {line!r}")

                else:
                    bname, bvalue = line[:idx], line[idx + 1 :]
                    name = bname.decode("utf8").strip()
                    value = bvalue.decode("utf8").strip()

                    state.headers[name] = value
                    continue

            if (length := state.content_length) == -1:
                return

            if len(state.buffer) < length:
                return

            content, state.buffer = state.buffer[:length], state.buffer[length:]
            message = JsonRPCMessage(
                headers=state.headers,
                body=json.loads(content),
                metadata={
                    "timestamp": datetime.now(tz=timezone.utc),
                    "source": source,
                    "session": "todo",
                },
            )

            state.headers = {}
            state.headers_complete = False

            if inspect.iscoroutine(res := self.handle(message)):
                task = asyncio.create_task(res)
                self._tasks.add(task)
                task.add_done_callback(self._tasks.discard)

    def stop(self):
        pass
