import argparse
import asyncio
import json
import pathlib
import threading
from datetime import datetime
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import aiosqlite
import appdirs
from rich.highlighter import ReprHighlighter
from rich.text import Text
from textual import events
from textual.app import App
from textual.app import ComposeResult
from textual.containers import Container
from textual.events import Ready
from textual.widgets import DataTable
from textual.widgets import Footer
from textual.widgets import Header
from textual.widgets import Tree
from textual.widgets import TreeNode

from lsp_devtools.record import setup_filter_args

from .client import Ping
from .client import TUIAgentClient
from .client import connect_to_agent


class ObjectViewer(Tree):
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


RPCData = Dict[int, Tuple[Optional[str], Optional[str], Optional[str]]]


class MessagesTable(DataTable):
    """Datatable used to display all messages between client and server"""

    def __init__(self, dbpath: pathlib.Path, viewer: ObjectViewer):
        super().__init__()

        self.dbpath = dbpath
        self.dbquery = "SELECT rowid, * FROM protocol WHERE rowid > ?"
        self.rpcdata: RPCData = {}
        self.max_row = -1

        self.viewer = viewer

        self.add_column("")
        self.add_column("Time")
        self.add_column("Source")
        self.add_column("ID")
        self.add_column("Method")

    def on_key(self, event: events.Key):

        if event.key != "enter":
            return

        rowid = int(self.data[self.cursor_row][0])
        params, result, error = self.rpcdata[rowid]

        if params:
            name = "params"
            message = json.loads(params)

        elif result:
            name = "result"
            message = json.loads(result)

        elif error:
            name = "error"
            message = json.loads(error)

        else:
            name = "data"
            message = {}

        self.viewer.set_object(name, message)

    async def update(self):
        """Trigger a re-run of the query to pull in new data."""

        async with aiosqlite.connect(self.dbpath) as conn:
            async with conn.execute(self.dbquery, (self.max_row,)) as cursor:
                async for row in cursor:
                    rowid = row[0]
                    timestamp = row[2]
                    source = row[3]
                    id_ = row[4]
                    method = row[5]
                    params = row[6]
                    result = row[7]
                    error = row[8]

                    self.rpcdata[rowid] = (params, result, error)

                    # Surely there's a more direct way to do this?
                    dt = datetime.fromtimestamp(timestamp)
                    time = dt.isoformat(timespec="milliseconds")
                    time = time[time.find("T") + 1 :]

                    self.add_row(str(rowid), time, source, id_, method)
                    self.max_row = rowid


class Sidebar(Container):
    pass


class LSPInspector(App):

    CSS_PATH = pathlib.Path(__file__).parent / "app.css"
    BINDINGS = [("ctrl+b", "toggle_sidebar", "Sidebar"), ("q", "quit", "Quit")]

    def __init__(self, dbpath: pathlib.Path, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.dbpath = dbpath
        """Where the data for the app is being held"""

        self.client: Optional[TUIAgentClient] = None
        """Client used to interact with the LSPAgent hosting the server we're
        inspecting."""

        self.loop: Optional[asyncio.AbstractEventLoop] = None
        """Accessed by the AgentClient to push messages into the UI"""

    def compose(self) -> ComposeResult:
        yield Header()

        viewer = ObjectViewer("")
        messages = MessagesTable(self.dbpath, viewer)

        yield Container(messages, Sidebar(viewer))
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
        self.loop = asyncio.get_running_loop()
        await self.update_table()

    async def on_ping(self, message: Ping):
        """Fired when the agent client receives new messages"""
        await self.update_table()

    async def update_table(self):
        table = self.query_one(MessagesTable)
        await table.update()

    async def action_quit(self):
        if self.client:
            self.client._stop_event.set()
        await super().action_quit()


def tui(args, extra: List[str]):

    dbpath = args.to_sqlite
    if not dbpath.parent.exists():
        dbpath.parent.mkdir(parents=True)

    app = LSPInspector(dbpath)
    client = connect_to_agent(args, app)
    app.client = client

    agent_thread = threading.Thread(
        name="AgentClient", target=client.start_ws_client, args=(args.host, args.port)
    )
    agent_thread.start()

    app.run()
    agent_thread.join()


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
        dest="to_sqlite",  # to be compatible with code borrowed from record command.
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

    setup_filter_args(cmd)
    cmd.set_defaults(run=tui)
