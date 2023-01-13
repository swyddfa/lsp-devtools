import asyncio
import logging
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import BinaryIO

from pygls.server import aio_readline

logger = logging.getLogger("lsp_devtools.agent")


def forward_message(source: str, dest: BinaryIO, message: bytes):
    """Forward the given message to the destination channel"""
    dest.write(message)
    dest.flush()

    # Log the full message
    logger.info(
        "%s",
        message.decode("utf8"),
        extra={"source": source},
    )


async def check_server_process(
    server_process: subprocess.Popen, stop_event: threading.Event
):
    """Ensure that the server process is still alive."""

    while not stop_event.is_set():
        retcode = server_process.poll()
        print(".")
        if retcode is not None:

            # Cancel any pending tasks.
            for task in asyncio.all_tasks():
                task.cancel(f"Server process exited with code: {retcode}")

            # Signal everything to stop.
            stop_event.set()

        await asyncio.sleep(0.1)


class Agent:
    """The Agent sits between a language server and its client, listening to messages
    enabling them to be recorded."""

    def __init__(self, server: subprocess.Popen, stdin: BinaryIO, stdout: BinaryIO):
        self.stdin = stdin
        self.stdout = stdout
        self.server_process = server
        self.stop_event = threading.Event()
        self.thread_pool_executor = ThreadPoolExecutor(
            max_workers=4,
            thread_name_prefix="LSP Traffic Worker ",
        )

    async def start(self):
        event_loop = asyncio.get_running_loop()

        # Connect stdin to the subprocess' stdin
        client_to_server = aio_readline(
            loop=event_loop,
            executor=self.thread_pool_executor,
            stop_event=self.stop_event,
            rfile=self.stdin,
            proxy=partial(forward_message, "client", self.server_process.stdin),
        )

        # Connect the subprocess' stdout to stdout
        server_to_client = aio_readline(
            loop=event_loop,
            executor=self.thread_pool_executor,
            stop_event=self.stop_event,
            rfile=self.server_process.stdout,
            proxy=partial(forward_message, "server", self.stdout),
        )

        # Run both connections concurrently.
        return await asyncio.gather(
            client_to_server,
            server_to_client,
            check_server_process(self.server_process, self.stop_event),
        )

    def stop(self):
        self.stop_event.set()
        self.thread_pool_executor.shutdown(wait=False, cancel_futures=True)

        try:
            self.server_process.terminate()
            ret = self.server_process.wait(timeout=1)
            print(f"Server process exited with code: {ret}")
        except TimeoutError:
            self.server_process.kill()

        # Need to close these to prevent open file warnings
        if self.server_process.stdin is not None:
            self.server_process.stdin.close()

        if self.server_process.stdout is not None:
            self.server_process.stdout.close()
