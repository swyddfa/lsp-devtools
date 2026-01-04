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
from textual.containers import Vertical
from textual.message import Message
from textual.widgets import Button
from textual.widgets import Footer

from lsp_devtools.cli.utils import LiveSqlHandler
from lsp_devtools.editor import Explorer
from lsp_devtools.editor import OutputWindow
from lsp_devtools.editor import Panel
from lsp_devtools.editor import TextEditorView
from lsp_devtools.inspector import MessageBrowser

from .client import LanguageClient
from .config import AppConfig
from .config import ConfigurationScreen

if typing.TYPE_CHECKING:
    from textual.app import ComposeResult
    from textual.widgets import DirectoryTree
    from textual.worker import Worker


class StderrReceived(Message):
    def __init__(self, data: bytes):
        super().__init__()
        self.data = data


@typing.final
class LSPClient(App[None]):
    """A simple LSP client."""

    DEFAULT_CSS = """
      .hidden {
        display: none;
      }

      #left-sidebar {
        dock: left;
        width: 15%;
      }

      #open-settings-btn {
        margin: 1;
        width: 100%;
      }

      MessageBrowser {
        dock: right;
        width: 30%;
      }

      Panel {
        padding-top: 1;
        height: 30%;
      }

      Footer {
        dock: bottom;
      }
    """

    BINDINGS = [
        ("ctrl+c", "quit"),
        ("f2", "toggle_explorer", "Explorer"),
        ("f5", "run_server", "Run Server"),
        ("f8", "toggle_panel", "Panel"),
        ("f12", "toggle_devtools", "Devtools"),
    ]

    def __init__(self, *args, config: AppConfig, **kwargs):
        super().__init__(*args, **kwargs)

        self.config: AppConfig = config
        self.client: LanguageClient | None = None
        self.server: Worker[None] | None = None

        self.db = LiveSqlHandler()
        self.db.app = self

    def compose(self) -> ComposeResult:
        # Main area
        yield TextEditorView()
        yield Panel()

        # Sidebars
        yield MessageBrowser()

        with Vertical(id="left-sidebar"):
            yield Explorer()
            yield Button("Settings", id="open-settings-btn")

        # Footer
        yield Footer()

    def action_open_settings(self):
        def maybe_update_config(new_config: AppConfig | None):
            if new_config is not None:
                # TODO: Restart server as required.
                self.config = new_config

        _ = self.push_screen(
            ConfigurationScreen(config=self.config), maybe_update_config
        )

    def action_toggle_explorer(self) -> None:
        explorer = self.query_one("#left-sidebar")
        is_visible = not explorer.has_class("hidden")

        if is_visible:
            explorer.add_class("hidden")

        else:
            explorer.remove_class("hidden")
            self.screen.set_focus(explorer)

    def action_toggle_devtools(self) -> None:
        devtools = self.query_one(MessageBrowser)
        is_visible = not devtools.has_class("hidden")

        if is_visible:
            devtools.add_class("hidden")

        else:
            devtools.remove_class("hidden")
            self.screen.set_focus(devtools)

    def action_toggle_panel(self) -> None:
        panel = self.query_one(Panel)
        is_visible = not panel.has_class("hidden")

        if is_visible:
            panel.add_class("hidden")

        else:
            panel.remove_class("hidden")
            self.screen.set_focus(panel)

    def action_run_server(self):
        if self.server is None:
            self.server = self.run_worker(self.start_server(), name="server-connection")
            return

        # Did the process exit?
        if self.server.is_finished:
            self.server = self.run_worker(self.start_server(), name="server-connection")
            return

        # TODO: Add logic for restarting the server process.

    def on_ready(self, event: events.Ready):
        # Auto start server if possible.
        if len(self.config.server.command) > 0:
            self.action_run_server()

    @on(LiveSqlHandler.MessageReceived)
    def on_message_received(self, event: LiveSqlHandler.MessageReceived):
        browser = self.query_one(MessageBrowser)
        browser.reload(follow=True)

    @on(StderrReceived)
    def on_stderr_received(self, event: StderrReceived):
        panel = self.query_one(Panel)
        log = panel.query_one("#stderr-window", OutputWindow)
        log.write(event.data)

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "open-settings-btn":
            self.action_open_settings()

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected):
        """Handle file-open."""
        editor = self.query_one(TextEditorView)
        editor.open_text_document(event.path)

    async def start_server(self):
        """Start the server and connect to it."""

        server_config = self.config.server
        if len(server_config.command) == 0:
            # TODO: Prompt user to set a command.
            return

        def stderr_handler(data: bytes):
            self.app.post_message(StderrReceived(data))

        self.client = LanguageClient(
            self.db,
            stderr_handler=stderr_handler,
            name="lsp-devtools",
            version=importlib.metadata.version("lsp-devtools"),
        )
        await self.client.start_io(*server_config.command)

        result = await self.client.initialize_async(
            types.InitializeParams(
                capabilities=types.ClientCapabilities(),
                process_id=os.getpid(),
                root_uri=uri.from_fs_path(os.getcwd()),
                workspace_folders=[
                    types.WorkspaceFolder(
                        uri=uri.from_fs_path(os.getcwd()), name="root"
                    )
                ],
            )
        )
        self.client.initialized(types.InitializedParams())


def client(args, extra: list[str]):
    # TODO: Read configs from file.
    config = AppConfig()

    # Allow for a server command to be passed on the cli.
    if len(extra) > 0:
        config.server.command = extra

    app = LSPClient(config=config)
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
