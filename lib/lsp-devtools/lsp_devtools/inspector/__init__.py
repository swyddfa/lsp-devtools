from __future__ import annotations

import argparse
import pathlib
import typing

import platformdirs
from textual import log
from textual import on
from textual.app import App
from textual.app import ComposeResult
from textual.events import Ready
from textual.message import Message
from textual.widgets import Footer
from textual.widgets import Header
from textual.widgets.tree import TreeNode

from lsp_devtools.agent import AgentServer
from lsp_devtools.agent import MessageSource
from lsp_devtools.handlers.jsonrpc import JsonRPCMessage
from lsp_devtools.handlers.sql import SqlHandler

from .message_table import MessageTable

if typing.TYPE_CHECKING:
    from typing import Any


class MessageReceived(Message):
    def __init__(self, message: JsonRPCMessage):
        self.message = message
        super().__init__()


@typing.final
class LSPInspector(App):
    """A textual app for inspecting an LSP session, either a live one or one that has
    been pre-recorded."""

    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
    ]

    def __init__(
        self,
        db: AppSqlHandler,
        server: AgentServer | None = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        db.app = self
        self.db = db
        """Holds recorded messages"""

        self.server = server
        """If set, expect to receive a live connection from the lsp-devtools agent."""

    def compose(self) -> ComposeResult:
        yield Header()
        yield MessageTable()

        yield Footer()

    # @on(MessageReceived)
    # def on_message_received(self, event: MessageReceived):
    #     log("handled")
    #     table = self.query_one(DataTable)

    #     message = event.message
    #     table.add_row(message.msg_id, message.method)

    async def on_ready(self, event: Ready):
        table = self.query_one(MessageTable)
        table.reload()

        if self.server is not None:
            self.run_worker(self.server.start_tcp(), name="lsp-connection", thread=True)

    async def action_quit(self):
        if self.server is not None:
            self.server.stop()
        await super().action_quit()


class AppSqlHandler(SqlHandler):
    def __init__(self, app: App | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = app

    def handle(self, message: JsonRPCMessage):
        super().handle(message)
        log("message")
        if self.app is not None:
            self.app.post_message(MessageReceived(message))


def inspector(args, extra: list[str]):
    server = None

    if args.session is not None:
        sql_handler = AppSqlHandler(dbpath=args.session)

    # Assume a live connection
    else:
        sql_handler = AppSqlHandler(dbpath=":memory:")
        server = AgentServer(
            handlers={
                MessageSource.CLIENT: sql_handler,
                MessageSource.SERVER: sql_handler,
            }
        )

    app = LSPInspector(server=server, db=sql_handler)
    app.run()


def cli(commands: argparse._SubParsersAction):
    cmd: argparse.ArgumentParser = commands.add_parser(
        "inspect",
        help="launch an interactive LSP session inspector",
        description="""\
This command opens a text user interface that can be used to inspect a LSP session
interactively.
""",
    )

    cmd.add_argument(
        "session",
        type=pathlib.Path,
        metavar="",
        help="inspect the pre-recorded session at the given path",
    )

    connect = cmd.add_argument_group(
        title="connection options",
        description="options that control the connection to the LSP Agent.",
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
    cmd.set_defaults(run=inspector)
