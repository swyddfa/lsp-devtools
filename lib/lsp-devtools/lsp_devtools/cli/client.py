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
from textual.message import Message
from textual.widgets import Footer

from lsp_devtools.cli.utils import LiveSqlHandler
from lsp_devtools.client import LanguageClient
from lsp_devtools.editor import Explorer
from lsp_devtools.editor import OutputWindow
from lsp_devtools.editor import Panel
from lsp_devtools.editor import TextEditorView
from lsp_devtools.inspector.message_browser import MessageBrowser

if typing.TYPE_CHECKING:
    from textual.app import ComposeResult
    from textual.widgets import DirectoryTree


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

      Explorer {
        dock: left;
        width: 15%;
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
        ("f8", "toggle_panel", "Panel"),
        ("f12", "toggle_devtools", "Devtools"),
    ]

    def __init__(self, *args, server_command: list[str], **kwargs):
        super().__init__(*args, **kwargs)

        self.server_command = server_command
        self.client: LanguageClient | None = None

        self.db = LiveSqlHandler()
        self.db.app = self

    def compose(self) -> ComposeResult:
        # Main area
        yield TextEditorView()
        yield Panel()

        # Sidebars
        yield MessageBrowser()
        yield Explorer()

        # Footer
        yield Footer()

    def action_toggle_explorer(self) -> None:
        explorer = self.query_one(Explorer)
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

    def on_ready(self, event: events.Ready):
        self.run_worker(self.start_server(), name="lsp-connection")

    @on(LiveSqlHandler.MessageReceived)
    def on_message_received(self, event: LiveSqlHandler.MessageReceived):
        browser = self.query_one(MessageBrowser)
        browser.reload(follow=True)

    @on(StderrReceived)
    def on_stderr_received(self, event: StderrReceived):
        panel = self.query_one(Panel)
        log = panel.query_one("#stderr-window", OutputWindow)
        log.write(event.data)

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected):
        """Handle file-open."""
        editor = self.query_one(TextEditorView)
        editor.open_text_document(event.path)

    async def start_server(self):
        """Start the server and connect to it."""

        def stderr_handler(data: bytes):
            self.app.post_message(StderrReceived(data))

        self.client = LanguageClient(
            self.db,
            stderr_handler=stderr_handler,
            name="lsp-devtools",
            version=importlib.metadata.version("lsp-devtools"),
        )
        await self.client.start_io(*self.server_command)

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
    if len(extra) == 0:
        raise ValueError(
            "Missing server command. (e.g. lsp-devtools client -- server-cmd --stdio)"
        )

    app = LSPClient(server_command=extra)
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
