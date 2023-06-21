import asyncio
import inspect
import logging
import re
import threading
from functools import partial
from typing import BinaryIO

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


# TODO: Upstream this?
async def aio_readline(stop_event, reader, message_handler):
    CONTENT_LENGTH_PATTERN = re.compile(rb"^Content-Length: (\d+)\r\n$")

    # Initialize message buffer
    message = []
    content_length = 0

    while not stop_event.is_set():
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
                logger.debug("Content length: %s", content_length)

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


async def get_streams(stdin, stdout):
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
        self.stop_event = threading.Event()

    async def start(self):
        # Get async versions of stdin/stdout
        reader, writer = await get_streams(self.stdin, self.stdout)

        # Connect stdin to the subprocess' stdin
        client_to_server = aio_readline(
            self.stop_event,
            reader,
            partial(forward_message, "client", self.server.stdin),
        )

        # Connect the subprocess' stdout to stdout
        server_to_client = aio_readline(
            self.stop_event,
            self.server.stdout,
            partial(forward_message, "server", writer),
        )

        # Run both connections concurrently.
        return await asyncio.gather(
            client_to_server,
            server_to_client,
        )

    async def stop(self):
        self.stop_event.set()

        try:
            self.server.terminate()
            ret = await self.server.wait()
            print(f"Server process exited with code: {ret}")
        except TimeoutError:
            self.server.kill()
