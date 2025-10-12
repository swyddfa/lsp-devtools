from __future__ import annotations

import asyncio
import logging
import threading
import typing

if typing.TYPE_CHECKING:
    from collections.abc import Awaitable
    from concurrent.futures import ThreadPoolExecutor
    from typing import BinaryIO
    from typing import Protocol

    class AsyncReader(Protocol):
        """An asynchronous reader."""

        def read(self, n: int = -1) -> Awaitable[bytes]: ...

        def readexactly(self, n: int) -> Awaitable[bytes]: ...

    class AsyncWriter(Protocol):
        """An asynchronous writer."""

        def close(self) -> Awaitable[None]: ...

        def write(self, data: bytes) -> Awaitable[None]: ...


logger = logging.getLogger(__name__)


class StdinAsyncReader:
    """Read from stdin asynchronously."""

    def __init__(self, stdin: BinaryIO, executor: ThreadPoolExecutor | None = None):
        self._stdin = stdin
        self._executor = executor
        self._lock = threading.Lock()
        self._buffer = bytearray()
        self._bytes_available = threading.Event()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._future: asyncio.Future[None] | None = None

    @property
    def loop(self):
        if self._loop is None:
            self._loop = asyncio.get_running_loop()

        return self._loop

    def _start_read_loop(self):
        """If required, start background task of reading from stdin."""
        if self._future is None:
            self._future = self.loop.run_in_executor(self._executor, self._read_loop)

        return self._future

    def _read_loop(self, n: int = -1):
        # Yes, I'm sure it's terribly inefficient to read one byte at a time.
        # However, I have no idea how to otherwise make sure that we don't hang waiting
        # for more bytes than are currently available.
        # logger.debug("stdin: loop start")
        while (b := self._stdin.read(1)) != b"":
            with self._lock:
                self._buffer += b
                self._bytes_available.set()
                # logger.debug("buffer: %r", len(self._buffer))
        # logger.debug("stdin: loop end")

    async def read(self, n: int = -1) -> bytes:
        # If the future is done, then the stream must be closed.
        if (fut := self._start_read_loop()).done():
            return b""

        await self.loop.run_in_executor(self._executor, self._bytes_available.wait)
        await self.loop.run_in_executor(self._executor, self._lock.acquire)

        try:
            length = min(n, len(self._buffer))
            if length == len(self._buffer):
                self._bytes_available.clear()

            data, self._buffer = self._buffer[:length], self._buffer[length:]
            logger.debug("chunk: %r, buffer: %r", len(data), len(self._buffer))

            return bytes(data)
        finally:
            self._lock.release()

    async def readexactly(self, n: int) -> bytes:
        self._start_read_loop()

        data = b""
        remainder = n
        while len(data) < n:
            chunk = await self.read(remainder)
            remainder -= len(chunk)
            data += chunk
            logger.debug("r: %r, data: %r", remainder, len(data))

        return data


class StdoutAsyncWriter:
    """Write to stdout asynchronously."""

    def __init__(self, stdout: BinaryIO, executor: ThreadPoolExecutor | None = None):
        self.stdout = stdout
        self._loop: asyncio.AbstractEventLoop | None = None
        self.executor = executor

    @property
    def loop(self):
        if self._loop is None:
            self._loop = asyncio.get_running_loop()

        return self._loop

    def close(self) -> Awaitable[None]:
        return self.loop.run_in_executor(self.executor, self.stdout.close)

    def _write(self, data: bytes):
        self.stdout.write(data)
        self.stdout.flush()

    def write(self, data: bytes) -> Awaitable[None]:
        return self.loop.run_in_executor(self.executor, self._write, data)


class AsyncStreamWriter:
    """Thin wrapper around an ``asyncio.StreamWriter`` to align it to the
    ``AsyncWriter`` protocol."""

    def __init__(self, writer: asyncio.StreamWriter):
        self.writer = writer

    def close(self) -> Awaitable[None]:
        self.writer.close()
        return asyncio.sleep(0)

    def write(self, data: bytes) -> Awaitable[None]:
        self.writer.write(data)
        return self.writer.drain()


async def get_stdio_streams(
    stdin: BinaryIO, stdout: BinaryIO
) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    """Convert blocking stdin/stdout streams into async streams.

    .. important::

       This method does NOT work on Windows
    """
    loop = asyncio.get_running_loop()

    reader = asyncio.StreamReader()
    read_protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: read_protocol, stdin)

    write_transport, write_protocol = await loop.connect_write_pipe(
        asyncio.streams.FlowControlMixin, stdout
    )
    writer = asyncio.StreamWriter(write_transport, write_protocol, reader, loop)
    return reader, writer
