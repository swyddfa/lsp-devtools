"""
This module is what enables the majority of lsp-devtools suite of tools.

       +---- LSP Client ---+        +---- LSP Agent ----+        +---- LSP Server ---+
       |                   |        | +---------------+ |        |                   |
       |                out|--------|>|in  Server  out|-|------->|in                 |
       |                   |        | +---------------+ |        |                   |
       |                 in|<-------|-|out Server   in|<|--------|out                |
       |                   |        | +---------------+ |        |                   |
       +-------------------+        +-------------------+        +-------------------+
"""

import asyncio
import json
import logging
import subprocess
import threading
from json.decoder import JSONDecodeError
from threading import Event
from typing import Any
from typing import BinaryIO

import websockets
from pygls.protocol import JsonRPCProtocol, default_converter
from pygls.server import Server
from websockets.client import WebSocketClientProtocol


logger = logging.getLogger(__name__)


class LSPAgent:
    """The Agent sits between a language server and its client, listening to messages
    enabling them to be recorded."""

    def __init__(self, server: subprocess.Popen, stdin: BinaryIO, stdout: BinaryIO):
        self.stdin = stdin
        self.stdout = stdout
        self.server_process = server

    def start(self):
        """Setup the connections between client and server and start it all running."""

        self.client_to_server = Server(
            protocol_cls=Passthrough, converter_factory=default_converter
        )
        self.client_to_server.lsp.source = "client"
        self.client_to_server_thread = threading.Thread(
            name="Client -> Server",
            target=self.client_to_server.start_io,
            args=(self.stdin, self.server_process.stdin),
        )
        self.client_to_server_thread.daemon = True

        self.server_to_client = Server(
            protocol_cls=Passthrough,
            loop=asyncio.new_event_loop(),
            converter_factory=default_converter,
        )
        self.server_to_client.lsp.source = "server"
        self.server_to_client_thread = threading.Thread(
            name="Server -> Client",
            target=self.server_to_client.start_io,
            args=(self.server_process.stdout, self.stdout),
        )
        self.server_to_client_thread.daemon = True

        self.client_to_server_thread.start()
        self.server_to_client_thread.start()

    def join(self):
        self.client_to_server_thread.join()
        self.server_to_client_thread.join()


class Passthrough(JsonRPCProtocol):
    """A JsonRPCProtocol implementation that simply forwards the messages it recevies
    while also logging them."""

    source: str

    def data_received(self, data: bytes):
        """A slightly modified version of the method found in upstream pygls.

        As well as immediately writing the data we receive to the transport, we also
        bypass pygls' message parsing code and log the raw json object.
        """
        logger.debug("Received %r", data)

        while len(data):

            # Forward on the data as we receive it
            self.transport.write(data)
            logger.debug(data.decode(self.CHARSET), extra={"source": self.source})

            # Append the incoming chunk to the message buffer
            self._message_buf.append(data)

            # Look for the body of the message
            message = b"".join(self._message_buf)
            found = JsonRPCProtocol.MESSAGE_PATTERN.fullmatch(message)

            body = found.group("body") if found else b""
            length = int(found.group("length")) if found else 1

            if len(body) < length:
                # Message is incomplete; bail until more data arrives
                return

            # Message is complete;
            # extract the body and any remaining data,
            # and reset the buffer for the next message
            body, data = body[:length], body[length:]
            self._message_buf = []

            # Log the full message
            logger.info(
                "%s",
                json.loads(body.decode(self.CHARSET)),
                extra={"source": self.source},
            )


class WebSocketClientTransportAdapter:
    """Protocol adapter for the WebSocket client interface."""

    def __init__(
        self, ws: WebSocketClientProtocol, loop: asyncio.AbstractEventLoop
    ):
        self._ws = ws
        self._loop = loop

    def close(self) -> None:
        """Stop the WebSocket server."""
        print("-- CLOSING --")
        self._loop.create_task(self._ws.close())

    def write(self, data: Any) -> None:
        """Create a task to write specified data into a WebSocket."""
        asyncio.ensure_future(self._ws.send(data))



class LSPAgentClient(Server):
    """Client for connecting to an LSPAgent instance."""

    def __init__(self):
        super().__init__(
            protocol_cls=JsonRPCProtocol, converter_factory=default_converter
        )

    def _report_server_error(self, error, source):
        # Bail on error
        self._stop_event.set()


    def start_ws_client(self, host: str, port: int):
        """Similar to ``start_ws``, but where we create a client connection rather than
        host a server."""

        self._stop_event = Event()
        self.lsp._send_only_body = True  # Don't send headers within the payload

        async def client_connection(host: str, port: int):
            """Create and run a client connection."""

            self._client = await websockets.connect(f"ws://{host}:{port}")
            self.lsp.transport = WebSocketClientTransportAdapter(self._client, self.loop)
            message = None

            try:
                while not self._stop_event.is_set():
                    try:
                        message = await asyncio.wait_for(self._client.recv(), timeout=0.5)
                        self.lsp._procedure_handler(
                            json.loads(message, object_hook=self.lsp._deserialize_message)
                        )
                    except JSONDecodeError:
                        print(message or "-- message not found --")
                        raise
                    except TimeoutError:
                        pass
                    except Exception:
                        raise

            finally:
                await self._client.close()

        try:
            asyncio.run(client_connection(host, port))
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()
