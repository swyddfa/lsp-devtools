import asyncio
import json
from json.decoder import JSONDecodeError
from threading import Event
from typing import Any
from typing import Optional

import websockets
from pygls.protocol import default_converter
from pygls.server import Server
from websockets.client import WebSocketClientProtocol

from lsp_devtools.agent.protocol import AgentProtocol


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


class AgentClient(Server):
    """Client for connecting to an LSPAgent instance."""

    lsp: AgentProtocol

    def __init__(self):
        super().__init__(
            protocol_cls=AgentProtocol, converter_factory=default_converter
        )
        self._client_buf = []
        self._server_buf = []

    def _report_server_error(self, error, source):
        # Bail on error
        # TODO: Report the actual error somehow
        self._stop_event.set()

    def feature(self, feature_name: str, options: Optional[Any] = None):
        return self.lsp.fm.feature(feature_name, options)

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
