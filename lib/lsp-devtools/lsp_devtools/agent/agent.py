from __future__ import annotations

import asyncio
import inspect
import logging
import re
import sys
import typing
from functools import partial

if typing.TYPE_CHECKING:
    from typing import BinaryIO
    from typing import Optional
    from typing import Set
    from typing import Tuple

logger = logging.getLogger("lsp_devtools.agent")


async def forward_message(source: str, dest: asyncio.StreamWriter, message: bytes):
    """Forward the given message to the destination channel"""
    dest.write(message)
    await dest.drain()

    # Log the full message
    logger.info(
        "%s",
        message.decode("utf8"),
        extra={"source": source},
    )


async def aio_readline(reader: asyncio.StreamReader, message_handler):
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
) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
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
        self, server: asyncio.subprocess.Process, stdin: BinaryIO, stdout: BinaryIO
    ):
        self.stdin = stdin
        self.stdout = stdout
        self.server = server

        self._tasks: Set[asyncio.Task] = set()
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None

    async def start(self):
        # Get async versions of stdin/stdout
        self.reader, self.writer = await get_streams(self.stdin, self.stdout)

        # Keep mypy happy
        assert self.server.stdin
        assert self.server.stdout

        # Connect stdin to the subprocess' stdin
        client_to_server = asyncio.create_task(
            aio_readline(
                self.reader,
                partial(forward_message, "client", self.server.stdin),
            ),
        )
        self._tasks.add(client_to_server)

        # Connect the subprocess' stdout to stdout
        server_to_client = asyncio.create_task(
            aio_readline(
                self.server.stdout,
                partial(forward_message, "server", self.writer),
            ),
        )
        self._tasks.add(server_to_client)

        # Run both connections concurrently.
        await asyncio.gather(
            client_to_server,
            server_to_client,
            self._watch_server_process(),
        )

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

        args = {}
        if sys.version_info.minor > 8:
            args["msg"] = "lsp-devtools agent is stopping."

        # Cancel the tasks connecting client to server
        for task in self._tasks:
            task.cancel(**args)

        if self.writer:
            self.writer.close()
