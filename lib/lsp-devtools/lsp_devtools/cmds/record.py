import argparse
import json
import logging
from typing import List
from typing import Optional

from rich.console import ConsoleRenderable
from rich.containers import Renderables
from rich.logging import RichHandler
from rich.panel import Panel
from rich.traceback import Traceback

from lsp_devtools.agent import LSPAgentClient

logger = logging.getLogger(__name__)


def obj_to_dict(obj):
    if hasattr(obj, '_asdict'):
        return {k: obj_to_dict(v) for k, v in obj._asdict().items()}

    if isinstance(obj, list):
        return [obj_to_dict(o) for o in obj]

    return obj


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
        self, *,
        record: logging.LogRecord,
        traceback: Optional[Traceback],
        message_renderable: "ConsoleRenderable"
    ) -> "ConsoleRenderable":
        """Render the complete log message, timestamps and all."""
        msg = record.msg

        # Override the log record's creation time with that of the lsp message.
        record.created = msg.timestamp

        # Delegate most of the rendering to the base RichHandler class.
        res = super().render(
            record=record, traceback=traceback, message_renderable=message_renderable
        )

        # Abuse the log level column to display the source of the message,
        color = "green" if msg.source == "client" else "blue"
        res.columns[1]._cells[0] = f"[bold][{color}]{msg.source.upper()}[/{color}][/bold]"

        return res

    def render_message(
        self, record: logging.LogRecord, message: str
    ) -> "ConsoleRenderable":
        msg = record.msg
        data = {}
        data_title = ""

        if msg.params:
            data = msg.params
            data_title = "params"

        if msg.result:
            data = msg.result
            data_title = "result"

        if msg.error:
            data = msg.error
            data_title = "error"

        fields = [
            f"id='{msg.id}'" if msg.id else "",
            f"method='{msg.method}'" if msg.method else "",
        ]

        msg_data = json.dumps(obj_to_dict(data), indent=2)
        return Renderables([
            self.highlighter(" ".join([f for f in fields if f])),
            Panel(self.highlighter(msg_data), title=data_title)
        ])


def log_message(params):
    logger.info(params, extra={'some': 'test'})


def setup_stdout_output():
    handler = RichLSPHandler(logging.INFO)

    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def record(args, extra: List[str]):

    client = LSPAgentClient()
    setup_stdout_output()

    client.lsp.fm.feature("$/lspMessage")(log_message)
    client.start_ws_client(args.host, args.port)

def cli(commands: argparse._SubParsersAction):
    cmd = commands.add_parser(
        "record",
        help="record an LSP session, requires the server be wrapped by an agent.",
        description="""\
This command connects to an LSP Agent allowing for messages sent
between client and server to be logged.
""",
    )  # type: argparse.ArgumentParser

    connect = cmd.add_argument_group(
        title="connection options",
        description="options that control the connection to the LSP Agent."
    )
    connect.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="the host that is hosting the agent."
    )
    connect.add_argument(
        "-p",
        "--port",
        type=int,
        default=8765,
        help="the port to connect to."
    )

    cmd.set_defaults(run=record)
