from __future__ import annotations

import asyncio
import inspect
import json
import typing
from collections import defaultdict
from datetime import datetime
from datetime import timezone

import attrs

from lsp_devtools.agent import MessageHeader
from lsp_devtools.agent import MessageSource

if typing.TYPE_CHECKING:
    from typing import Any
    from typing import Literal
    from typing import Protocol

    JsonRPCMessageType = Literal[
        "request", "response", "result", "error", "notification"
    ]

    class JsonRPCFilter(Protocol):
        def match(self, message: JsonRPCMessage) -> JsonRPCMessage | None:
            """Returns the given message if it matches the filter."""


@attrs.define
class JsonRPCMessage:
    """A Json-RPC message."""

    metadata: dict[str, Any]

    headers: dict[str, str]

    body: dict[str, Any]

    def __getitem__(self, key: str):
        return self.headers[key]

    @classmethod
    def client(cls, body: dict[str, Any]):
        """Helper for constructing a message sent by the client"""
        headers = {
            "Content-Length": str(len(json.dumps(body))),
        }

        return cls(
            headers=headers, body=body, metadata={"source": MessageSource.CLIENT}
        )

    @classmethod
    def server(cls, body: dict[str, Any]):
        """Helper for constructing a message sent by the server"""
        headers = {
            "Content-Length": str(len(json.dumps(body))),
        }

        return cls(
            headers=headers, body=body, metadata={"source": MessageSource.SERVER}
        )

    @property
    def timestamp(self) -> datetime | None:
        if (dt := self.metadata.get("timestamp")) is None:
            return None

        if isinstance(dt, str):
            return datetime.fromisoformat(dt)

    @property
    def source(self) -> MessageSource | None:
        return self.metadata.get("source")

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

    def to_bytes(self) -> bytes:
        """Convert the message to bytes"""
        body = json.dumps(self.body)
        lines: list[str] = []

        for key, value in self.headers.items():
            lines.append(f"{key}: {value}")

        lines.append("")
        lines.append(body)

        return "\r\n".join(lines).encode()

    def to_wire_format(self) -> bytes:
        """Encode the message according to how we send bytes over the wire."""
        msg = self.to_bytes()
        return b"".join([MessageHeader.pack(self.metadata["source"], len(msg)), msg])


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

    def __init__(self, filter: JsonRPCFilter | None = None):
        self._filter: JsonRPCFilter | None = filter
        self._parsers: dict[MessageSource, ParserState] = defaultdict(ParserState)
        self._tasks: set[asyncio.Task[Any]] = set()

    def _handle_message(self, message: JsonRPCMessage):
        if self._filter and self._filter.match(message) is None:
            return

        self.handle(message)

    def handle(self, message: JsonRPCMessage):
        """Handle the messages."""
        raise NotImplementedError

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

                if (idx := line.find(b":")) == -1:
                    raise ValueError(f"Invalid message header: {line!r}")

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

            if inspect.iscoroutine(res := self._handle_message(message)):
                task = asyncio.create_task(res)
                self._tasks.add(task)
                task.add_done_callback(self._tasks.discard)

    def stop(self):
        pass
