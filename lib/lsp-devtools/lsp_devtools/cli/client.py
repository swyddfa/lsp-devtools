from __future__ import annotations

import argparse
import importlib.metadata
import os
import typing

from lsprotocol import types
from pygls import uris as uri
from textual import events
from textual import on
from textual.app import App
from textual.widgets import Footer

from lsp_devtools.cli.utils import LiveSqlHandler
from lsp_devtools.client import LanguageClient
from lsp_devtools.editor import TextEditorView
from lsp_devtools.inspector.message_browser import MessageBrowser

if typing.TYPE_CHECKING:
    from textual.app import ComposeResult


class LSPClient(App[None]):
    """A simple LSP client."""

    DEFAULT_CSS = """
      .hidden {
        display: none;
      }

      MessageBrowser {
        dock: right;
        width: 30%;
      }
    """

    BINDINGS = [
        ("ctrl+c", "quit"),
        ("f12", "toggle_devtools", "Devtools"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        yield TextEditorView()

        browser = MessageBrowser()
        browser.add_class("hidden")
        yield browser

        yield Footer()

    def action_toggle_devtools(self) -> None:
        devtools = self.query_one(MessageBrowser)
        is_visible = not devtools.has_class("hidden")

        if is_visible:
            devtools.add_class("hidden")

        else:
            devtools.remove_class("hidden")
            self.screen.set_focus(devtools)

    def on_ready(self, event: events.Ready):
        self.run_worker(self.start_server(), name="lsp-connection", thread=True)

    @on(LiveSqlHandler.MessageReceived)
    def on_message_received(self, event: LiveSqlHandler.MessageReceived):
        browser = self.query_one(MessageBrowser)
        browser.reload(follow=True)

    async def start_server(self):
        self.db = LiveSqlHandler()
        self.db.app = self

        client = LanguageClient(
            self.db,
            name="lsp-devtools",
            version=importlib.metadata.version("lsp-devtools"),
        )
        await client.start_io("esbonio")

        result = await client.initialize_async(
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

        client.initialized(types.InitializedParams())


def client(args, extra: list[str]):
    # if len(extra) == 0:
    #     raise ValueError("Missing server command.")

    app = LSPClient()
    app.run()


def cli(commands: argparse._SubParsersAction):
    cmd: argparse.ArgumentParser = commands.add_parser(
        "client",
        help="launch an LSP client with built in inspector",
        description="""\
Open a simple text editor to drive a given language server.
""",
    )

    cmd.set_defaults(run=client)
