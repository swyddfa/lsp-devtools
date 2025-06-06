from __future__ import annotations

import asyncio
import enum
import inspect
import json
import logging
import struct
import sys
import typing
from datetime import datetime
from datetime import timezone
from uuid import uuid4

import attrs

from .io_ import AsyncStreamWriter
from .io_ import StdinAsyncReader
from .io_ import StdoutAsyncWriter

if typing.TYPE_CHECKING:
    from collections.abc import Coroutine
    from concurrent.futures import ThreadPoolExecutor
    from typing import Any
    from typing import BinaryIO
    from typing import Callable
    from typing import Union

    from .io_ import AsyncReader
    from .io_ import AsyncWriter

    DataHandler = Callable[[bytes], Union[None, Coroutine[Any, Any, None]]]


UTC = timezone.utc
logger = logging.getLogger("lsp_devtools.agent")
MessageHeader = struct.Struct("!BI")


class MessageSource(enum.IntEnum):
    """Indicates if a message came from the client or the server."""

    Agent = enum.auto()
    """Messages coming from the agent itself"""

    Client = enum.auto()
    """Messages coming from the language client"""

    Server = enum.auto()
    """Messages coming from the langiage server"""


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

    # TODO: Reuse me
    if False:
        # Forward the message as-is to the client/server
        dest.write(message)

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

    return RPCMessage(headers, body)


class Agent:
    """The Agent sits between a language server and its client, listening to messages
    enabling them to be recorded."""

    def __init__(
        self,
        server: asyncio.subprocess.Process,
        stdin: BinaryIO,
        stdout: BinaryIO,
        handler: DataHandler,
        executor: ThreadPoolExecutor | None = None,
    ):
        self.server = server
        self.handler = handler
        self.session_id = str(uuid4())
        self._tasks: set[asyncio.Task[Any]] = set()

        self.reader: AsyncReader = StdinAsyncReader(stdin, executor)
        self.writer: AsyncWriter = StdoutAsyncWriter(stdout, executor)

    async def start(self):
        if (server_stdin := self.server.stdin) is None:
            raise RuntimeError("Missing stdin for server process")

        if (server_stdout := self.server.stdout) is None:
            raise RuntimeError("Missing stdout for server process")

        # Connect stdin to the subprocess' stdin
        client_to_server = asyncio.create_task(
            self.connect_streams(
                self.reader,
                AsyncStreamWriter(server_stdin),
                MessageSource.Client,
            ),
        )
        self._tasks.add(client_to_server)

        # Connect the subprocess' stdout to stdout
        server_to_client = asyncio.create_task(
            self.connect_streams(
                server_stdout,
                self.writer,
                MessageSource.Server,
            ),
        )
        self._tasks.add(server_to_client)

        # Run both connections concurrently.
        await asyncio.gather(
            client_to_server,
            server_to_client,
            self._watch_server_process(),
        )

    async def connect_streams(
        self, source: AsyncReader, dest: AsyncWriter, origin: MessageSource
    ):
        """Forward bytes from the source to the destination, while simultaneously
        passing them to the handler function"""

        logger.debug('%r: loop start', origin)
        while (data := await source.read(1024)) != b"":
            # Send the data onto the server/client as-is
            logger.debug("%r: read: %r bytes", origin, len(data))
            await dest.write(data)

            # Forward the captured data onto the handler
            header = MessageHeader.pack(origin.value, len(data))
            payload = b"".join([header, data])

            if inspect.isawaitable(res := self.handler(payload)):
                task = asyncio.create_task(res)
                self._tasks.add(task)
                task.add_done_callback(self._tasks.discard)

        logger.debug("%r: loop broken", origin)

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
