import argparse
import asyncio
import threading
from datetime import datetime
from typing import List
from typing import Optional

from textual.app import App, ComposeResult
from textual.events import Ready
from textual.binding import Binding
from textual.message import Message, MessageTarget
from textual.widgets import DataTable, Header, Footer

from lsp_devtools.agent import LSPAgentClient


class Receive(Message):
    """Receive a message from the lsp agent."""

    def __init__(self, sender: MessageTarget, content):
        self.content = content
        super().__init__(sender)


class MessagesTable(DataTable):

    def __init__(self):
        super().__init__()

        self.add_column("Time")
        self.add_column("Source")
        self.add_column("ID")
        self.add_column("Method")


    def add_message(self, message):

        # Surely there's a more direct way to do this??
        dt = datetime.fromtimestamp(message.timestamp)
        time = dt.isoformat(timespec='milliseconds')
        time = time[time.find('T') + 1:]

        source = "→" if message.source == "client" else "←"

        self.add_row(
            time,
            source,
            str(message.id or ""),
            str(message.method or ""),
        )


class LSPInspector(App):

    BINDINGS = [
        Binding("q", "quit", "Quit")
    ]

    def __init__(
        self, client, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)

        self.client: LSPAgentClient = client
        """Client used to interact with the LSPAgent hosting the server we're inspecting"""

        self.loop: Optional[asyncio.AbstractEventLoop] = None
        """Accessed by the LSPAgentClient to push messages into the UI"""

    def compose(self) -> ComposeResult:
        yield Header()
        yield MessagesTable()
        yield Footer()

    async def on_ready(self, event: Ready):
        self.loop = asyncio.get_running_loop()

    async def on_receive(self, message: Receive):
        msg = message.content

        table = self.query_one(MessagesTable)
        table.add_message(msg)

    async def action_quit(self):
        self.client._stop_event.set()
        await super().action_quit()


def tui(args, extra: List[str]):

    client = LSPAgentClient()
    app = LSPInspector(client)

    pending_coros = []

    # LSPAgentClient is based on pygls.server.Server, so the usual @server.feature()
    # helper is not available.
    @client.lsp.fm.feature("$/lspMessage")
    def handle_message(params):
        coro = app.post_message(Receive(app, params))

        # The event loop only becomes available once the on_ready event has fired
        # and the UI has bootstrapped itself. So it's possible we recevie
        # messages before the app is ready to accept them.
        if app.loop is None:
            pending_coros.append(coro)
            return

        # Be sure to push any pending messages first.
        while len(pending_coros) > 0:
            asyncio.run_coroutine_threadsafe(pending_coros.pop(), app.loop)

        asyncio.run_coroutine_threadsafe(coro, app.loop)

    agent_thread = threading.Thread(
        name="LSPAgentClient",
        target=client.start_ws_client,
        args=(args.host, args.port)
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

    connect = cmd.add_argument_group(
        title="connection options",
        description="options that control the connection to the LSP Agent."
    )
    connect.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="the host that is hosting the agent."
    )
    connect.add_argument(
        "-p",
        "--port",
        type=int,
        default=8765,
        help="the port to connect to."
    )

    cmd.set_defaults(run=tui)
