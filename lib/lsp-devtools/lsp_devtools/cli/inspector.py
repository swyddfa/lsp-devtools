from __future__ import annotations

import argparse
import pathlib
import typing

from textual import on
from textual.app import App
from textual.app import ComposeResult
from textual.events import Ready
from textual.widgets import DataTable
from textual.widgets import Footer
from textual.widgets import Header

from lsp_devtools.agent import AgentServer
from lsp_devtools.agent import MessageSource
from lsp_devtools.cli.utils import LiveSqlHandler
from lsp_devtools.handlers.sql import SqlHandler
from lsp_devtools.inspector.message_browser import MessageBrowser


@typing.final
class LSPInspector(App[None]):
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

    @on(LiveSqlHandler.MessageReceived)
    def on_message_received(self, event: LiveSqlHandler.MessageReceived):
        browser = self.query_one(MessageBrowser)
        # Only jump to the latest message when the user is already following the
        # tail; otherwise preserve their selected row. See #247.
        browser.reload(follow=browser.is_following_tail())

    async def on_ready(self, event: Ready):
        browser = self.query_one(MessageBrowser)
        browser.reload()

        table = browser.query_one(DataTable)
        table.focus()

        if self.server is not None:
            self.run_worker(self.server.start_tcp(), name="lsp-connection")

    async def action_quit(self):
        if self.server is not None:
            self.server.stop()
        await super().action_quit()


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
