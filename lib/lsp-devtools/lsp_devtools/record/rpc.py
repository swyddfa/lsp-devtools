from __future__ import annotations

import asyncio
from datetime import datetime
from datetime import timezone

from rich.console import Console
from rich.highlighter import ReprHighlighter
from rich.table import Table

from lsp_devtools.agent import AgentServer
from lsp_devtools.agent import MessageSource
from lsp_devtools.handlers.file import FileHandler
from lsp_devtools.handlers.jsonrpc import JsonRPCHandler
from lsp_devtools.handlers.jsonrpc import JsonRPCMessage
from lsp_devtools.handlers.sql import SqlHandler

from .filters import JsonRPCFilter
from .formatters import JsonRPCFormatter
from .visualize import TrafficVisualiser

EXPORTERS = {
    ".html": ("save_html", {}),
    ".svg": ("save_svg", {"title": ""}),
    ".txt": ("save_text", {}),
}


class RecordFileHandler(FileHandler):
    """A FileHandler with extra eye candy for running as a cli command."""

    def __init__(self, visualizer: TrafficVisualiser, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.visualizer = visualizer

    def handle(self, message: JsonRPCMessage):
        super().handle(message)
        self.visualizer.emit(message.metadata["source"])


def setup_file_output(args, console: Console) -> AgentServer:
    visualizer = TrafficVisualiser(console)

    if not args.to_file.parent.exists():
        args.to_file.parent.mkdir(parents=True)

    handler = RecordFileHandler(
        fp=args.to_file.open("w"),
        filter=get_message_filter(args),
        formatter=get_message_formatter(args, default="{message:jsonl}"),
        visualizer=visualizer,
    )

    return AgentServer(
        handlers={
            MessageSource.CLIENT: handler,
            MessageSource.SERVER: handler,
        },
    )


class RecordSqlHandler(SqlHandler):
    """A SqlHandler with extra eye candy for running as a cli command."""

    def __init__(self, visualizer: TrafficVisualiser, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.visualizer = visualizer

    def handle(self, message: JsonRPCMessage):
        super().handle(message)
        self.visualizer.emit(message.metadata["source"])


def setup_sqlite_output(args, console: Console) -> AgentServer:
    visualizer = TrafficVisualiser(console)

    if not args.to_sqlite.parent.exists():
        args.to_sqlite.parent.mkdir(parents=True)

    handler = RecordSqlHandler(
        dbpath=args.to_sqlite,
        filter=get_message_filter(args),
        visualizer=visualizer,
    )

    return AgentServer(
        handlers={
            MessageSource.CLIENT: handler,
            MessageSource.SERVER: handler,
        },
    )


class RichHandler(JsonRPCHandler):
    """A JSON-RPC handler that uses rich to render messages nicely."""

    def __init__(self, console: Console, formatter: JsonRPCFormatter, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.console = console
        self.highlighter = ReprHighlighter()
        self.content_formatter = formatter

    def handle(self, message: JsonRPCMessage):
        if (content := self.content_formatter.format(message)) is None:
            return

        table = Table.grid(padding=(0, 1))
        table.expand = True
        table.add_column(style="log.time")
        table.add_column(style="log.level")
        table.add_column(style="log.message", ratio=1, overflow="fold")

        if message.metadata["source"] == MessageSource.CLIENT:
            source = "[red]CLIENT[/red]"

        elif message.metadata["source"] == MessageSource.SERVER:
            source = "[blue]SERVER[/blue]"

        else:
            source = ""

        dt = message.metadata.get("timestamp", datetime.now(tz=timezone.utc))
        table.add_row(f"{dt:%H:%M:%S}", source, self.highlighter(content))
        self.console.print(table)


def setup_stdout_output(args, console: Console) -> AgentServer:
    """Return a server instance that's configured for writing messages to the console."""

    handler = RichHandler(
        console=console,
        formatter=get_message_formatter(args, default="{message}"),
        filter=get_message_filter(args),
    )

    server = AgentServer(
        handlers={
            MessageSource.CLIENT: handler,
            MessageSource.SERVER: handler,
        },
    )

    return server


def record_rpc(args):
    console = Console(record=args.save_output is not None)

    if args.to_file:
        server = setup_file_output(args, console)

    elif args.to_sqlite:
        server = setup_sqlite_output(args, console)

    else:
        server = setup_stdout_output(args, console)

    server.persistent = args.on_disconnect != "exit"

    try:
        host = args.host
        port = args.port

        print(f"Waiting for connection on {host}:{port}...", end="\r", flush=True)
        asyncio.run(server.start_tcp(host, port))
    except asyncio.CancelledError:
        pass
    except KeyboardInterrupt:
        server.stop()

    if console is not None:
        console.show_cursor(True)

        if args.save_output is not None:
            destination = args.save_output
            exporter_name, kwargs = EXPORTERS.get(destination.suffix, (None, None))
            if exporter_name is None:
                console.print(f"Unable to save output to '{destination.suffix}' files")
                return

            exporter = getattr(console, exporter_name)
            exporter(str(destination), **kwargs)


def get_message_formatter(args, default: str):
    """Convert cli arguments to a JsonRPCFormatter instance."""
    fallback = default if args.keep_unformatted else None
    formats = args.format_message or [default]

    return JsonRPCFormatter(formats, fallback)


def get_message_filter(args):
    """Convert cli arguments to a JsonRPCFilter filter instance."""
    return JsonRPCFilter(
        message_source=args.message_source,
        include_message_types=args.include_message_types,
        exclude_message_types=args.exclude_message_types,
        include_methods=args.include_methods,
        exclude_methods=args.exclude_methods,
    )
