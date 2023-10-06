import asyncio
from typing import Any
from typing import Optional

import stamina
from pygls.client import JsonRPCClient
from pygls.client import aio_readline
from pygls.protocol import default_converter

from lsp_devtools.agent.protocol import AgentProtocol

# from websockets.client import WebSocketClientProtocol


# class WebSocketClientTransportAdapter:
#     """Protocol adapter for the WebSocket client interface."""

#     def __init__(self, ws: WebSocketClientProtocol, loop: asyncio.AbstractEventLoop):
#         self._ws = ws
#         self._loop = loop

#     def close(self) -> None:
#         """Stop the WebSocket server."""
#         print("-- CLOSING --")
#         self._loop.create_task(self._ws.close())

#     def write(self, data: Any) -> None:
#         """Create a task to write specified data into a WebSocket."""
#         asyncio.ensure_future(self._ws.send(data))


class AgentClient(JsonRPCClient):
    """Client for connecting to an AgentServer instance."""

    protocol: AgentProtocol

    def __init__(self):
        super().__init__(
            protocol_cls=AgentProtocol, converter_factory=default_converter
        )
        self.connected = False

    def _report_server_error(self, error, source):
        # Bail on error
        # TODO: Report the actual error somehow
        self._stop_event.set()

    def feature(self, feature_name: str, options: Optional[Any] = None):
        return self.protocol.fm.feature(feature_name, options)

    # TODO: Upstream this... or at least something equivalent.
    async def start_tcp(self, host: str, port: int):
        # The user might not have started the server app immediately and since the
        # agent will live as long as the wrapper language server we may as well
        # try indefinitely.
        retries = stamina.retry_context(
            on=OSError,
            attempts=None,
            timeout=None,
            wait_initial=1,
            wait_max=60,
        )
        async for attempt in retries:
            with attempt:
                reader, writer = await asyncio.open_connection(host, port)

        self.protocol.connection_made(writer)  # type: ignore[arg-type]
        connection = asyncio.create_task(
            aio_readline(self._stop_event, reader, self.protocol.data_received)
        )
        self.connected = True
        self._async_tasks.append(connection)

    # TODO: Upstream this... or at least something equivalent.
    # def start_ws(self, host: str, port: int):
    #     self.protocol._send_only_body = True  # Don't send headers within the payload

    #     async def client_connection(host: str, port: int):
    #         """Create and run a client connection."""

    #         self._client = await websockets.connect(  # type: ignore
    #             f"ws://{host}:{port}"
    #         )
    #         loop = asyncio.get_running_loop()
    #         self.protocol.transport = WebSocketClientTransportAdapter(
    #             self._client, loop
    #         )
    #         message = None

    #         try:
    #             while not self._stop_event.is_set():
    #                 try:
    #                     message = await asyncio.wait_for(
    #                         self._client.recv(), timeout=0.5
    #                     )
    #                     self.protocol._procedure_handler(
    #                         json.loads(
    #                             message,
    #                             object_hook=self.protocol._deserialize_message
    #                         )
    #                     )
    #                 except JSONDecodeError:
    #                     print(message or "-- message not found --")
    #                     raise
    #                 except TimeoutError:
    #                     pass
    #                 except Exception:
    #                     raise

    #         finally:
    #             await self._client.close()

    #     try:
    #         asyncio.run(client_connection(host, port))
    #     except KeyboardInterrupt:
    #         pass
