from __future__ import annotations

import asyncio
import sys
import typing

from rich.console import Console
from textual import events
from textual.app import App
from textual.widgets import Footer
from textual.widgets import Log

from lsp_devtools.agent import AgentServer
from lsp_devtools.agent import MessageSource

from .visualize import TrafficVisualiser

if typing.TYPE_CHECKING:
    import pathlib
    from typing import BinaryIO

    from textual.app import ComposeResult


class LogWidgetHandler:
    """Message handler that writes captured data to the corresponding Log widget."""

    def __init__(self, app: App, name: str):
        self.app = app
        self.name = name

    def feed(self, data: bytes, source: MessageSource):
        log = self.app.query_one(f"#{self.name}", Log)
        log.write(data.decode())

    def stop(self):
        pass


class FileHandler:
    """Message handler that writes captured data to the given file."""

    def __init__(self, fp: BinaryIO, visualizer: TrafficVisualiser):
        self.fp = fp
        self.visualizer = visualizer

    def feed(self, data: bytes, source: MessageSource):
        self.fp.write(data)
        self.visualizer.emit(source)

    def stop(self):
        self.fp.close()


class RawRecordApp(App):
    """Simple app for "recording" raw traffic sent between client and server."""

    DEFAULT_CSS = """\
    Log {
      border: round $foreground-darken-3;
    }

    #client {
      border-title-color: $primary;

    }

    #server {
      border-title-color: $accent;
    }
    """

    def __init__(self, host: str, port: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.host = host
        self.port = port

    def compose(self) -> ComposeResult:
        client_log = Log(id="client")
        client_log.border_title = "Client"

        server_log = Log(id="server")
        server_log.border_title = "Server"

        yield client_log
        yield server_log
        yield Footer()

    async def on_ready(self, event: events.Ready):
        server = AgentServer(
            handlers={
                MessageSource.CLIENT: LogWidgetHandler(self, "client"),
                MessageSource.SERVER: LogWidgetHandler(self, "server"),
            }
        )
        self.run_worker(server.start_tcp(self.host, self.port))


def record_raw(args):
    """Record raw output sent between the client and server."""

    if args.to_file:
        console = Console()
        visualizer = TrafficVisualiser(console)

        base: pathlib.Path = args.to_file

        client_file = base.with_stem(f"{base.stem}-CLIENT")
        server_file = base.with_stem(f"{base.stem}-SERVER")

        client_fp = client_file.open("wb")
        server_fp = server_file.open("wb")

        server = AgentServer(
            persistent=args.on_disconnect != "exit",
            handlers={
                MessageSource.CLIENT: FileHandler(client_fp, visualizer),
                MessageSource.SERVER: FileHandler(server_fp, visualizer),
            },
        )

        try:
            host = args.host
            port = args.port

            print(f"Waiting for connection on {host}:{port}...", end="\r", flush=True)
            asyncio.run(server.start_tcp(args.host, args.port))
        finally:
            client_fp.close()
            server_fp.close()

    elif args.to_sqlite:
        print("Recording raw output to SQLite is not supported", file=sys.stderr)
        return 1

    else:
        app = RawRecordApp(args.host, args.port)
        return app.run()
