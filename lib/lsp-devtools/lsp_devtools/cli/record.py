from __future__ import annotations

import argparse
import pathlib

from lsp_devtools.record.raw import record_raw
from lsp_devtools.record.rpc import record_rpc


def start_recording(args, extra: list[str] | None):
    if args.capture_raw:
        return record_raw(args)
    else:
        return record_rpc(args)


def setup_filter_args(cmd: argparse.ArgumentParser):
    """Add arguments that can be used to filter messages."""

    filter_ = cmd.add_argument_group(
        title="filter options",
        description=(
            "select which messages to record, mutliple options will be ANDed together. "
            "Does not apply to raw message capture"
        ),
    )
    filter_.add_argument(
        "--message-source",
        default="both",
        choices=["client", "server", "both"],
        help="only include messages from the given source",
    )
    filter_.add_argument(
        "--include-message-type",
        action="append",
        default=[],
        dest="include_message_types",
        choices=["request", "response", "result", "error", "notification"],
        help="only include the given message type(s)",
    )
    filter_.add_argument(
        "--exclude-message-type",
        action="append",
        dest="exclude_message_types",
        default=[],
        choices=["request", "response", "result", "error", "notification"],
        help="omit the given message type(s)",
    )
    filter_.add_argument(
        "--include-method",
        action="append",
        dest="include_methods",
        default=[],
        metavar="METHOD",
        help="only include the given messages for the given method(s)",
    )
    filter_.add_argument(
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
Listen for a connection from the lsp-devtools agent and record the traffic it captures""",
    )

    connect = cmd.add_argument_group(
        title="server options",
        description="how and where the server should listen for connections",
    )
    connect.add_argument(
        "--bind",
        dest="host",
        type=str,
        default="localhost",
        help="where to listen for connections from",
    )
    connect.add_argument(
        "-p", "--port", type=int, default=8765, help="the port to listen on"
    )
    connect.add_argument(
        "--on-disconnect",
        default="continue",
        choices=["continue", "exit"],
        help="how should the server react to a client disconnect (default: continue)",
    )

    capture = cmd.add_mutually_exclusive_group()
    capture.add_argument(
        "--capture-raw",
        action="store_true",
        help="capture the raw data send between LSP client and server.",
    )
    capture.add_argument(
        "--capture-rpc",
        default=True,
        action="store_true",
        help="capture and parse the rpc messages sent between LSP client and server.",
    )

    setup_filter_args(cmd)
    format_ = cmd.add_argument_group(
        title="formatting options",
        description=(
            "control how the recorded messages are formatted "
            "(does not apply to SQLite output or raw message capture)"
        ),
    )
    format_.add_argument(
        "-f",
        "--format-message",
        action="append",
        help=(
            "format messages according to given format string, "
            "can be given multiple times, in which case the first valid string will be "
            "applied. "
            "By default, messages which fail to format will be excluded, "
            "see --keep-unformatted"
        ),
    )

    format_.add_argument(
        "--keep-unformatted",
        action="store_true",
        help=(
            "preserve messages that fail to format using any supplied format string. "
            "These will be rendered with the default format string"
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
