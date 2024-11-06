from __future__ import annotations

import argparse
import asyncio
import logging
import os
import pathlib
from uuid import uuid4

import platformdirs
from lsprotocol import types
from pygls import uris as uri
from textual import events
from textual import on
from textual.app import App
from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.containers import Vertical
from textual.widgets import DirectoryTree
from textual.widgets import Footer
from textual.widgets import Header

from lsp_devtools.agent import logger
from lsp_devtools.database import Database
from lsp_devtools.database import DatabaseLogHandler
from lsp_devtools.inspector import MessagesTable
from lsp_devtools.inspector import MessageViewer

from .editor import EditorView
from .lsp import LanguageClient


class Explorer(DirectoryTree):
    @on(DirectoryTree.FileSelected)
    def open_file(self, event: DirectoryTree.FileSelected):
        if not self.parent:
            return

        editor = self.parent.query_one(EditorView)
        editor.open_file(event.path)
        editor.focus()


class Devtools(Vertical):
    pass


class LSPClient(App):
    """A simple LSP client for use with language servers."""

    CSS_PATH = pathlib.Path(__file__).parent / "app.css"
    BINDINGS = [
        ("f2", "toggle_explorer", "Explorer"),
        ("f12", "toggle_devtools", "Devtools"),
    ]

    def __init__(
        self, db: Database, server_command: list[str], session: str, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)

        self.db = db
        db.app = self

        self.session = session
        self.server_command = server_command
        self.lsp_client = LanguageClient()

        self._async_tasks: list[asyncio.Task] = []

    def compose(self) -> ComposeResult:
        message_viewer = MessageViewer("")
        messages_table = MessagesTable(
            self.db, message_viewer, session=self.lsp_client.session_id
        )

        yield Header()
        yield Explorer(".")
        yield EditorView(self.lsp_client)
        devtools = Devtools(ScrollableContainer(messages_table), message_viewer)
        devtools.add_class("-hidden")
        yield devtools
        yield Footer()

    def action_toggle_devtools(self) -> None:
        devtools = self.query_one(Devtools)
        is_visible = not devtools.has_class("-hidden")

        if is_visible:
            self.screen.focus_next()
            devtools.add_class("-hidden")

        else:
            devtools.remove_class("-hidden")
            self.screen.set_focus(devtools)

    def action_toggle_explorer(self) -> None:
        explorer = self.query_one(Explorer)
        is_visible = not explorer.has_class("-hidden")

        if is_visible and explorer.has_focus:
            self.screen.focus_next()
            explorer.add_class("-hidden")

        else:
            explorer.remove_class("-hidden")
            self.screen.set_focus(explorer)

    async def on_ready(self, event: events.Ready):
        # Start the lsp server.
        self.run_worker(self.start_lsp_server())

    async def start_lsp_server(self):
        """Initialize the lsp server session."""

        await self.lsp_client.start_io(self.server_command[0], *self.server_command[1:])
        result = await self.lsp_client.initialize_async(
            types.InitializeParams(
                capabilities=types.ClientCapabilities(),
                process_id=os.getpid(),
                root_uri=uri.from_fs_path(os.getcwd()),
            )
        )

        if info := result.server_info:
            name = info.name
            version = info.version or ""
            self.log(f"Connected to server: {name} {version}")

        self.lsp_client.initialized(types.InitializedParams())

    @on(Database.Update)
    async def update_table(self, event: Database.Update):
        table = self.query_one(MessagesTable)
        await table.update()

    async def action_quit(self):
        await self.lsp_client.shutdown_async(None)
        self.lsp_client.exit(None)
        await self.lsp_client.stop()
        await super().action_quit()


def client(args, extra: list[str]):
    if len(extra) == 0:
        raise ValueError("Missing server command.")

    db = Database(args.dbpath)

    session = str(uuid4())
    dbhandler = DatabaseLogHandler(db)
    dbhandler.setLevel(logging.INFO)

    logger.setLevel(logging.INFO)
    logger.addHandler(dbhandler)

    app = LSPClient(db, session=session, server_command=extra)
    app.run()

    asyncio.run(db.close())


def cli(commands: argparse._SubParsersAction):
    cmd: argparse.ArgumentParser = commands.add_parser(
        "client",
        help="launch an LSP client with built in inspector",
        description="""\
Open a simple text editor to drive a given language server.
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

    cmd.set_defaults(run=client)
