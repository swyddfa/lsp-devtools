from __future__ import annotations

import asyncio
import inspect
import json
import logging
import re
import sys
import typing
from datetime import datetime
from datetime import timezone
from functools import partial
from uuid import uuid4

import attrs

if typing.TYPE_CHECKING:
    from collections.abc import Coroutine
    from typing import Any
    from typing import BinaryIO
    from typing import Callable
    from typing import Union

    from pygls.io_ import AsyncReader

    MessageHandler = Callable[[bytes], Union[None, Coroutine[Any, Any, None]]]

UTC = timezone.utc
logger = logging.getLogger("lsp_devtools.agent")


@attrs.define
class RPCMessage:
    """A Json-RPC message."""

    headers: dict[str, str]

    body: dict[str, Any]

    def __getitem__(self, key: str):
        return self.headers[key]


def parse_rpc_message(data: bytes) -> RPCMessage:
    """Parse a JSON-RPC message from the given set of bytes."""

    headers: dict[str, str] = {}
    body: dict[str, Any] | None = None
    headers_complete = False

    for line in data.split(b"\r\n"):
        if line == b"":
            if "Content-Length" not in headers:
                raise ValueError("Missing 'Content-Length' header")

            headers_complete = True
            continue

        if headers_complete:
            length = int(headers["Content-Length"])
            if len(line) != length:
                raise ValueError("Incorrect 'Content-Length'")

            body = json.loads(line)
            continue

        if (idx := line.find(b":")) < 0:
            raise ValueError(f"Invalid header: {line!r}")

        name, value = line[:idx], line[idx + 1 :]
        headers[name.decode("utf8").strip()] = value.decode("utf8").strip()

    if body is None:
        raise ValueError("Missing message body")

    return RPCMessage(headers, body)


async def aio_readline(reader: AsyncReader, message_handler: MessageHandler):
    CONTENT_LENGTH_PATTERN = re.compile(rb"^Content-Length: (\d+)\r\n$")

    # Initialize message buffer
    message = []
    content_length = 0

    while True:
        # Read a header line
        header = await reader.readline()
        if not header:
            break
        message.append(header)

        # Extract content length if possible
        if not content_length:
            match = CONTENT_LENGTH_PATTERN.fullmatch(header)
            if match:
                content_length = int(match.group(1))

        # Check if all headers have been read (as indicated by an empty line \r\n)
        if content_length and not header.strip():
            # Read body
            body = await reader.readexactly(content_length)
            if not body:
                break
            message.append(body)

            # Pass message to protocol, optionally async
            result = message_handler(b"".join(message))
            if inspect.isawaitable(result):
                await result

            # Reset the buffer
            message = []
            content_length = 0


async def get_streams(
    stdin, stdout
) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    """Convert blocking stdin/stdout streams into async streams."""
    loop = asyncio.get_running_loop()

    reader = asyncio.StreamReader()
    read_protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: read_protocol, stdin)

    write_transport, write_protocol = await loop.connect_write_pipe(
        asyncio.streams.FlowControlMixin, stdout
    )
    writer = asyncio.StreamWriter(write_transport, write_protocol, reader, loop)
    return reader, writer


class Agent:
    """The Agent sits between a language server and its client, listening to messages
    enabling them to be recorded."""

    def __init__(
        self,
        server: asyncio.subprocess.Process,
        stdin: BinaryIO,
        stdout: BinaryIO,
        handler: MessageHandler,
    ):
        self.stdin = stdin
        self.stdout = stdout
        self.server = server
        self.handler = handler
        self.session_id = str(uuid4())

        self._tasks: set[asyncio.Task] = set()
        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None

    async def start(self):
        # Get async versions of stdin/stdout
        self.reader, self.writer = await get_streams(self.stdin, self.stdout)

        # Keep mypy happy
        if self.server.stdin is None or self.server.stdout is None:
            raise RuntimeError("Unable to find server I/O streams")

        # Connect stdin to the subprocess' stdin
        client_to_server = asyncio.create_task(
            aio_readline(
                self.reader,
                partial(self.forward_message, "client", self.server.stdin),
            ),
        )
        self._tasks.add(client_to_server)

        # Connect the subprocess' stdout to stdout
        server_to_client = asyncio.create_task(
            aio_readline(
                self.server.stdout,
                partial(self.forward_message, "server", self.writer),
            ),
        )
        self._tasks.add(server_to_client)

        # Run both connections concurrently.
        await asyncio.gather(
            client_to_server,
            server_to_client,
            self._watch_server_process(),
        )

    async def forward_message(
        self, source: str, dest: asyncio.StreamWriter, message: bytes
    ):
        """Forward the given message to the destination channel"""

        # Forward the message as-is to the client/server
        dest.write(message)
        await dest.drain()

        # Include some additional metadata before passing it onto the devtool.
        # TODO: How do we make sure we choose the same encoding as `message`?
        now = datetime.now(tz=UTC).isoformat()
        fields = [
            f"Message-Source: {source}\r\n".encode(),
            f"Message-Session: {self.session_id}\r\n".encode(),
            f"Message-Timestamp: {now}\r\n".encode(),
            message,
        ]

        if inspect.iscoroutine(res := self.handler(b"".join(fields))):
            task = asyncio.create_task(res)
            self._tasks.add(task)
            task.add_done_callback(self._tasks.discard)

    async def _watch_server_process(self):
        """Once the server process exits, ensure that the agent is also shutdown."""
        ret = await self.server.wait()
        print(f"Server process exited with code: {ret}", file=sys.stderr)
        await self.stop()

    async def stop(self):
        # Kill the server process if necessary.
        if self.server.returncode is None:
            try:
                self.server.terminate()
                await asyncio.wait_for(self.server.wait(), timeout=5)  # s
            except TimeoutError:
                self.server.kill()

        # Cancel the tasks connecting client to server
        for task in self._tasks:
            logger.debug("cancelling: %s", task)
            task.cancel(msg="lsp-devtools agent is stopping.")

        if self.writer:
            self.writer.close()
