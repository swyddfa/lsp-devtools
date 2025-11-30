from __future__ import annotations

import argparse
import pathlib
import tempfile
import typing

from textual import on
from textual.app import App
from textual.app import ComposeResult
from textual.events import Ready
from textual.message import Message
from textual.widgets import DataTable
from textual.widgets import Footer
from textual.widgets import Header

from lsp_devtools.agent import AgentServer
from lsp_devtools.agent import MessageSource
from lsp_devtools.handlers.jsonrpc import JsonRPCMessage
from lsp_devtools.handlers.sql import SqlHandler

from .message_browser import MessageBrowser


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

    DEFAULT_CSS = """
      MessageBrowser {
        height: 1fr;
      }
    """

    def __init__(
        self,
        db: SqlHandler,
        server: AgentServer | None = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.db = db
        """Holds recorded messages"""

        self.server = server
        """If set, expect to receive a live connection from the lsp-devtools agent."""

    def compose(self) -> ComposeResult:
        yield Header()
        yield MessageBrowser()

        yield Footer()

    @on(MessageReceived)
    def on_message_received(self, event: MessageReceived):
        browser = self.query_one(MessageBrowser)
        browser.reload(follow=True)

    async def on_ready(self, event: Ready):
        browser = self.query_one(MessageBrowser)
        browser.reload()

        table = browser.query_one(DataTable)
        table.focus()

        if self.server is not None:
            self.run_worker(self.server.start_tcp(), name="lsp-connection", thread=True)

    async def action_quit(self):
        if self.server is not None:
            self.server.stop()
        await super().action_quit()


class LiveSqlHandler(SqlHandler):
    """A SqlHandler with a textual app reference so it can trigger a refresh when
    messages are received."""

    def __init__(self, dbpath: None | pathlib.Path = None, *args, **kwargs):
        if dbpath is None:
            # In order to have concurrent access to a SQLite db, it must be backed by a file
            # https://sqlite.org/pragma.html#pragma_locking_mode
            self._dbdir = tempfile.TemporaryDirectory()
            dbpath = pathlib.Path(self._dbdir.name, "session.db")

        super().__init__(*args, dbpath=dbpath, **kwargs)
        self.app: App | None = None

    def __del__(self):
        super().__del__()
        self._dbdir.cleanup()

    def handle(self, message: JsonRPCMessage):
        super().handle(message)

        if self.app is not None:
            self.app.post_message(MessageReceived(message))


def inspector(args, extra: list[str]):
    server = None

    if args.session is not None:
        sql_handler = SqlHandler(dbpath=args.session)
        app = LSPInspector(db=sql_handler)

    # Assume a live connection
    else:
        sql_handler = LiveSqlHandler()
        server = AgentServer(
            handlers={
                MessageSource.CLIENT: sql_handler,
                MessageSource.SERVER: sql_handler,
            }
        )
        app = LSPInspector(server=server, db=sql_handler)
        sql_handler.app = app

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
        nargs="?",
        default=None,
        type=pathlib.Path,
        metavar="DB",
        help="inspect the pre-recorded session in the given SQLite DB",
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
