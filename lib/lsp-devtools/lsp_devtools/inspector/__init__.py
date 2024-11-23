from __future__ import annotations

import argparse
import asyncio
import logging
import pathlib
import typing
from functools import partial

import platformdirs
from rich.highlighter import ReprHighlighter
from rich.text import Text
from textual import on
from textual.app import App
from textual.app import ComposeResult
from textual.containers import Container
from textual.containers import ScrollableContainer
from textual.events import Ready
from textual.widgets import DataTable
from textual.widgets import Footer
from textual.widgets import Header
from textual.widgets import Tree
from textual.widgets.tree import TreeNode

from lsp_devtools.agent import AgentServer
from lsp_devtools.agent import parse_rpc_message
from lsp_devtools.database import Database
from lsp_devtools.handlers import LspMessage

if typing.TYPE_CHECKING:
    from typing import Any


logger = logging.getLogger(__name__)


class MessageViewer(Tree):
    """Used to inspect the fields of an object."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.highlighter = ReprHighlighter()

    def set_object(self, name: str, obj: Any):
        self.clear()
        self.root.set_label(name)
        self.walk_object(name, self.root, obj)

    def walk_object(self, label: str, node: TreeNode, obj: Any):
        if isinstance(obj, dict):
            node.expand()
            for field, value in obj.items():
                child = node.add(field)
                self.walk_object(field, child, value)

        elif isinstance(obj, list):
            node.expand()
            for idx, value in enumerate(obj):
                child_label = self.highlighter(str(idx))
                child = node.add(child_label)
                self.walk_object(str(idx), child, value)

        else:
            node.allow_expand = False
            node.set_label(Text.assemble(label, " = ", self.highlighter(repr(obj))))


class MessagesTable(DataTable):
    """Datatable used to display all messages between client and server"""

    def __init__(self, db: Database, viewer: MessageViewer, session=None):
        super().__init__()

        self.db = db

        self.rpcdata: dict[int, LspMessage] = {}
        self.max_row = 0
        self.session: str | None = session

        self.viewer = viewer

        self.cursor_type = "row"

        self.add_column("")
        self.add_column("Time")
        self.add_column("Source")
        self.add_column("ID")
        self.add_column("Method")

    @on(DataTable.RowHighlighted)
    def show_object(self, event: DataTable.RowHighlighted):
        """Show the message object on the currently highlighted row."""
        if event.cursor_row < 0:
            return

        rowid = int(self.get_row_at(event.cursor_row)[0])
        if (message := self.rpcdata.get(rowid, None)) is None:
            return

        name = ""
        obj = {}

        if message.params:
            name = "params"
            obj = message.params

        elif message.result:
            name = "result"
            obj = message.result

        elif message.error:
            name = "error"
            obj = message.error

        self.viewer.set_object(name, obj)

    def _get_query_params(self):
        """Return the set of query parameters to use when populating the table."""
        query: dict[str, Any] = dict(max_row=self.max_row)

        if self.session is not None:
            query["session"] = self.session

        return query

    async def update(self):
        """Trigger a re-run of the query to pull in new data."""

        query_params = self._get_query_params()
        messages = await self.db.get_messages(**query_params)
        for idx, message in messages:
            self.max_row = idx
            self.rpcdata[idx] = message

            time = message.timestamp[message.timestamp.find("T") + 1 :]
            self.add_row(str(idx), time, message.source, message.id, message.method)

        self.move_cursor(row=self.row_count, animate=True)


class Sidebar(Container):
    pass


class LSPInspector(App):
    CSS_PATH = pathlib.Path(__file__).parent / "app.css"
    BINDINGS = [
        ("ctrl+b", "toggle_sidebar", "Sidebar"),
        ("ctrl+c", "quit", "Quit"),
    ]

    def __init__(self, db: Database, server: AgentServer, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.db = db
        db.app = self

        self.server = server
        """Server used to manage connections to lsp servers."""

        self._async_tasks: list[asyncio.Task] = []

    def compose(self) -> ComposeResult:
        yield Header()

        viewer = MessageViewer("")
        messages = MessagesTable(self.db, viewer)
        yield Container(ScrollableContainer(messages), Sidebar(viewer))
        yield Footer()

    def action_toggle_sidebar(self) -> None:
        sidebar = self.query_one(Sidebar)
        self.set_focus(None)

        if sidebar.has_class("-hidden"):
            sidebar.remove_class("-hidden")
        else:
            if sidebar.query("*:focus"):
                self.screen.set_focus(None)
            sidebar.add_class("-hidden")

    async def on_ready(self, event: Ready):
        self._async_tasks.append(
            asyncio.create_task(self.server.start_tcp("localhost", 8765))
        )
        table = self.query_one(MessagesTable)
        await table.update()

    @on(Database.Update)
    async def update_table(self, event: Database.Update):
        table = self.query_one(MessagesTable)
        await table.update()

    async def action_quit(self):
        self.server.stop()
        await self.db.close()
        await super().action_quit()


async def handle_message(db: Database, data: bytes):
    """Handle messages received from the connected lsp server."""

    try:
        rpc = parse_rpc_message(data)
    except ValueError:
        # TODO: error reporting
        return

    session = rpc["Message-Session"]
    timestamp = rpc["Message-Timestamp"]
    source = rpc["Message-Source"]

    await db.add_message(session, timestamp, source, rpc.body)


def inspector(args, extra: list[str]):
    db = Database(args.dbpath)
    server = AgentServer(handler=partial(handle_message, db))

    app = LSPInspector(db, server)
    app.run()


def cli(commands: argparse._SubParsersAction):
    cmd: argparse.ArgumentParser = commands.add_parser(
        "inspect",
        help="launch an interactive LSP session inspector",
        description="""\
This command opens a text user interface that can be used to inspect and
manipulate an LSP session interactively.
""",
    )

    default_db = pathlib.Path(
        platformdirs.user_cache_dir(appname="lsp-devtools", appauthor="swyddfa"),
        "sessions.db",
    )
    cmd.add_argument(
        "--dbpath",
        type=pathlib.Path,
        metavar="DB",
        default=default_db,
        help="the database path to use",
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
