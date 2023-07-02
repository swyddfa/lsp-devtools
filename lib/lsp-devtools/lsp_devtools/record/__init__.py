import argparse
import asyncio
import json
import logging
import pathlib
from functools import partial
from logging import LogRecord
from typing import List
from typing import Optional

from rich.console import Console
from rich.console import ConsoleRenderable
from rich.logging import RichHandler
from rich.traceback import Traceback

from lsp_devtools.agent import MESSAGE_TEXT_NOTIFICATION
from lsp_devtools.agent import AgentServer
from lsp_devtools.agent import MessageText
from lsp_devtools.agent import parse_rpc_message
from lsp_devtools.handlers.sql import SqlHandler

from .filters import LSPFilter

EXPORTERS = {
    ".html": ("save_html", {}),
    ".svg": ("save_svg", {"title": ""}),
    ".txt": ("save_text", {}),
}
logger = logging.getLogger(__name__)


class RichLSPHandler(RichHandler):
    def __init__(self, level: int, log_time_format="%X", **kwargs):
        super().__init__(
            level=level,
            show_path=False,
            log_time_format=log_time_format,
            omit_repeated_times=False,
            **kwargs,
        )

    def render(
        self,
        *,
        record: logging.LogRecord,
        traceback: Optional[Traceback],
        message_renderable: "ConsoleRenderable",
    ) -> "ConsoleRenderable":
        # Delegate most of the rendering to the base RichHandler class.
        res = super().render(
            record=record, traceback=traceback, message_renderable=message_renderable
        )

        # Abuse the log level column to display the source of the message,
        source = record.__dict__["source"]
        color = "red" if source == "client" else "blue"
        message_source = f"[bold][{color}]{source.upper()}[/{color}][/bold]"
        res.columns[1]._cells[0] = message_source  # type: ignore

        return res

    def format(self, record: LogRecord) -> str:
        # Pretty print json messages
        if isinstance(record.args, dict):
            record.args = (json.dumps(record.args, indent=2),)
        return super().format(record)


def log_raw_message(ls: AgentServer, message: MessageText):
    """Push raw messages through the logging system."""
    logger.info(message.text, extra={"source": message.source})


def log_rpc_message(ls: AgentServer, message: MessageText):
    """Push parsed json-rpc messages through the logging system"""

    logfn = partial(logger.info, "%s", extra={"source": message.source})
    parse_rpc_message(ls, message, logfn)


def setup_stdout_output(args) -> Console:
    """Log to stdout."""

    console = Console(record=args.save_output is not None)
    handler = RichLSPHandler(level=logging.INFO, console=console)
    handler.addFilter(
        LSPFilter(
            message_source=args.message_source,
            include_message_types=args.include_message_types,
            exclude_message_types=args.exclude_message_types,
            include_methods=args.include_methods,
            exclude_methods=args.exclude_methods,
            formatter=args.format_message,
        )
    )

    logger.addHandler(handler)
    return console


def setup_file_output(args):
    handler = logging.FileHandler(filename=str(args.to_file))
    handler.setLevel(logging.INFO)
    handler.addFilter(
        LSPFilter(
            message_source=args.message_source,
            include_message_types=args.include_message_types,
            exclude_message_types=args.exclude_message_types,
            include_methods=args.include_methods,
            exclude_methods=args.exclude_methods,
            formatter=args.format_message,
        )
    )

    logger.addHandler(handler)


def setup_sqlite_output(args):
    handler = SqlHandler(args.to_sqlite)
    handler.setLevel(logging.INFO)
    handler.addFilter(
        LSPFilter(
            message_source=args.message_source,
            include_message_types=args.include_message_types,
            exclude_message_types=args.exclude_message_types,
            include_methods=args.include_methods,
            exclude_methods=args.exclude_methods,
        )
    )

    logger.addHandler(handler)


def start_recording(args, extra: List[str]):
    server = AgentServer()
    log_func = log_raw_message if args.capture_raw_output else log_rpc_message
    logger.setLevel(logging.INFO)
    server.feature(MESSAGE_TEXT_NOTIFICATION)(log_func)

    console: Optional[Console] = None
    host = args.host
    port = args.port

    if args.to_file:
        setup_file_output(args)

    elif args.to_sqlite:
        setup_sqlite_output(args)

    else:
        console = setup_stdout_output(args)

    try:
        print(f"Waiting for connection on {host}:{port}...", end="\r", flush=True)
        asyncio.run(server.start_tcp(host, port))
    except asyncio.CancelledError:
        pass
    except KeyboardInterrupt:
        pass

    if console is not None and args.save_output is not None:
        destination = args.save_output
        exporter_name, kwargs = EXPORTERS.get(destination.suffix, (None, None))
        if exporter_name is None:
            console.print(f"Unable to save output to '{destination.suffix}' files")
            return

        exporter = getattr(console, exporter_name)
        exporter(str(destination), **kwargs)


def setup_filter_args(cmd: argparse.ArgumentParser):
    """Add arguments that can be used to filter messages."""

    filter = cmd.add_argument_group(
        title="filter options",
        description=(
            "select which messages to record, mutliple options will be ANDed together. "
            "Does not apply to raw message capture"
        ),
    )
    filter.add_argument(
        "--message-source",
        default="both",
        choices=["client", "server", "both"],
        help="only include messages from the given source",
    )
    filter.add_argument(
        "--include-message-type",
        action="append",
        default=[],
        dest="include_message_types",
        choices=["request", "response", "result", "error", "notification"],
        help="only include the given message type(s)",
    )
    filter.add_argument(
        "--exclude-message-type",
        action="append",
        dest="exclude_message_types",
        default=[],
        choices=["request", "response", "result", "error", "notification"],
        help="omit the given message type(s)",
    )
    filter.add_argument(
        "--include-method",
        action="append",
        dest="include_methods",
        default=[],
        metavar="METHOD",
        help="only include the given messages for the given method(s)",
    )
    filter.add_argument(
        "--exclude-method",
        action="append",
        dest="exclude_methods",
        default=[],
        metavar="METHOD",
        help="omit messages for the given method(s)",
    )


def cli(commands: argparse._SubParsersAction):
    cmd: argparse.ArgumentParser = commands.add_parser(
        "record",
        help="record a JSON-RPC session.",
        description="""\
This command starts a JSON-RPC server allowing for a client to connect (over TCP by
default) and push messages to it and have them be recorded.
""",
    )

    connect = cmd.add_argument_group(
        title="connection options", description="how to connect to the LSP agent"
    )
    connect.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="the host that is hosting the agent.",
    )
    connect.add_argument(
        "-p", "--port", type=int, default=8765, help="the port to connect to."
    )

    capture = cmd.add_mutually_exclusive_group()
    capture.add_argument(
        "--capture-raw-output",
        action="store_true",
        help="capture the raw output from client and server.",
    )
    capture.add_argument(
        "--capture-rpc-output",
        default=True,
        action="store_true",
        help="capture the rpc messages sent between client and server.",
    )

    setup_filter_args(cmd)
    format = cmd.add_argument_group(
        title="formatting options",
        description=(
            "control how the recorded messages are formatted "
            "(does not apply to SQLite output or raw message capture)"
        ),
    )
    format.add_argument(
        "-f",
        "--format-message",
        default="",
        help=(
            "format messages according to given format string, "
            "see example commands above for syntax. "
            "Messages which fail to format will be excluded"
        ),
    )

    output = cmd.add_argument_group(
        title="output options",
        description="control where the captured messages are sent to",
    )
    output.add_argument(
        "--to-file",
        default=None,
        metavar="FILE",
        type=pathlib.Path,
        help="save messages to a file",
    )
    output.add_argument(
        "--to-sqlite",
        default=None,
        metavar="FILE",
        type=pathlib.Path,
        help="save messages to a SQLite DB",
    )
    output.add_argument(
        "--save-output",
        default=None,
        metavar="DEST",
        type=pathlib.Path,
        help=(
            "only applies when printing messages to the console. "
            "This makes use of the rich.Console's export feature to save its output in "
            "HTML, SVG or plain text format. The format used will be picked "
            "automatically based on the desintation's file extension."
        ),
    )

    cmd.set_defaults(run=start_recording)


def _enable_pygls_logging():
    pygls_log = logging.getLogger("pygls")
    pygls_log.setLevel(logging.DEBUG)
    pygls_log.addHandler(RichHandler(level=logging.DEBUG))
