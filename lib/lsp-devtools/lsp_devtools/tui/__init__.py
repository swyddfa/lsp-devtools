import argparse
import asyncio
import json
import logging
import pathlib
import re
from datetime import datetime
from typing import Any
from typing import Dict
from typing import List

import appdirs
from rich.highlighter import ReprHighlighter
from rich.text import Text
from textual import events
from textual import log
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

from lsp_devtools.agent import MESSAGE_TEXT_NOTIFICATION
from lsp_devtools.agent import AgentServer
from lsp_devtools.agent import MessageText
from lsp_devtools.handlers import LspMessage

from .database import Database
from .database import PingMessage

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

    def __init__(self, db: Database, viewer: MessageViewer):
        super().__init__()

        self.db = db
        self.rpcdata: Dict[int, LspMessage] = {}
        self.max_row = 0

        self.viewer = viewer

        self.cursor_type = "row"

        self.add_column("")
        self.add_column("Time")
        self.add_column("Source")
        self.add_column("ID")
        self.add_column("Method")

    def on_key(self, event: events.Key):
        if event.key != "enter":
            return

        rowid = int(self.get_row_at(self.cursor_row)[0])
        message = self.rpcdata[rowid]
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

    async def update(self):
        """Trigger a re-run of the query to pull in new data."""

        messages = await self.db.get_messages(self.max_row - 1)
        for message in messages:
            self.max_row += 1
            self.rpcdata[self.max_row] = message

            # Surely there's a more direct way to do this?
            dt = datetime.fromtimestamp(message.timestamp)
            time = dt.isoformat(timespec="milliseconds")
            time = time[time.find("T") + 1 :]

            self.add_row(
                str(self.max_row), time, message.source, message.id, message.method
            )

        self.move_cursor(row=self.max_row, animate=True)


class Sidebar(Container):
    pass


class LSPInspector(App):
    CSS_PATH = pathlib.Path(__file__).parent / "app.css"
    BINDINGS = [("ctrl+b", "toggle_sidebar", "Sidebar"), ("ctrl+c", "quit", "Quit")]

    def __init__(self, db: Database, server: AgentServer, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.db = db
        self.db.app = self
        """Where the data for the app is being held"""

        self.server = server
        """Server used to manage connections to lsp servers."""

        self._async_tasks = []

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

    @on(PingMessage)
    async def on_ping(self, message: PingMessage):
        await self.update_table()

    async def on_ready(self, event: Ready):
        self._async_tasks.append(
            asyncio.create_task(self.server.start_tcp("localhost", 8765))
        )
        await self.update_table()

    async def update_table(self):
        table = self.query_one(MessagesTable)
        await table.update()

    async def action_quit(self):
        await self.server.stop()
        await self.db.close()
        await super().action_quit()


MESSAGE_PATTERN = re.compile(
    r"^(?:[^\r\n]+\r\n)*"
    + r"Content-Length: (?P<length>\d+)\r\n"
    + r"(?:[^\r\n]+\r\n)*\r\n"
    + r"(?P<body>{.*)",
    re.DOTALL,
)


async def handle_message(ls: AgentServer, message: MessageText):
    """Handle messages received from the connected lsp server."""

    data = message.text
    message_buf = ls._client_buffer if message.source == "client" else ls._server_buffer

    while len(data):
        # Append the incoming chunk to the message buffer
        message_buf.append(data)

        # Look for the body of the message
        msg = "".join(message_buf)
        found = MESSAGE_PATTERN.fullmatch(msg)

        body = found.group("body") if found else ""
        length = int(found.group("length")) if found else 1

        if len(body) < length:
            # Message is incomplete; bail until more data arrives
            return

        # Message is complete;
        # extract the body and any remaining data,
        # and reset the buffer for the next message
        body, data = body[:length], body[length:]
        message_buf.clear()

        rpc = json.loads(body)
        await ls.db.add_message(message.session, message.timestamp, message.source, rpc)


def setup_server(db: Database):
    server = AgentServer()
    server.db = db
    server.feature(MESSAGE_TEXT_NOTIFICATION)(handle_message)
    return server


def tui(args, extra: List[str]):
    db = Database(args.dbpath)
    server = setup_server(db)

    app = LSPInspector(db, server)
    app.run()


def cli(commands: argparse._SubParsersAction):
    cmd: argparse.ArgumentParser = commands.add_parser(
        "tui",
        help="launch TUI",
        description="""\
This command opens a text user interface that can be used to inspect and
manipulate an LSP session interactively.
""",
    )

    default_db = pathlib.Path(
        appdirs.user_cache_dir(appname="lsp-devtools", appauthor="swyddfa"),
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
    cmd.set_defaults(run=tui)
