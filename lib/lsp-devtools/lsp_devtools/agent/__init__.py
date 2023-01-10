import argparse
import asyncio
import logging
import subprocess
import sys
import threading
from typing import List

from .agent import Agent
from .agent import logger
from .client import AgentClient
from .client import parse_rpc_message
from .protocol import MESSAGE_TEXT_NOTIFICATION
from .protocol import MessageText
from .server import AgentServer

__all__ = [
    "Agent",
    "AgentClient",
    "AgentServer",
    "logger",
    "MESSAGE_TEXT_NOTIFICATION",
    "MessageText",
    "parse_rpc_message",
]


class WSHandler(logging.Handler):
    """Logging handler that forwards captured LSP messages through to the web socket
    client."""

    def __init__(self, server: AgentServer, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.server = server

    def emit(self, record: logging.LogRecord):
        message = MessageText(
            text=record.args[0],  # type: ignore
            source=record.__dict__["source"],
        )
        self.server.lsp.message_text_notification(message)


def run_agent(args, extra: List[str]):

    if extra is None:
        print("Missing server start command", file=sys.stderr)
        return 1

    process = subprocess.Popen(extra, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    agent = Agent(process, sys.stdin.buffer, sys.stdout.buffer)

    server = AgentServer()
    handler = WSHandler(server)
    handler.setLevel(logging.INFO)

    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    agent_thread = threading.Thread(
        target=asyncio.run,
        args=(agent.start(),),
    )
    agent_thread.start()

    try:
        server.start_ws(args.host, args.port)
    finally:
        agent.stop()


def cli(commands: argparse._SubParsersAction):
    cmd: argparse.ArgumentParser = commands.add_parser(
        "agent",
        help="instrument an LSP session",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
This command runs the given language server as a subprocess, wrapping it in a
websocket server allowing all traffic to be inspected by some client.

To wrap a server, supply its start command after all other agent options and
preceeded by a `--`, for example:

    lsp-devtools agent -p 1234 -- python -m esbonio

Wrapping a language server with this command is required to enable the
majority of the lsp-devtools suite of tools.

       ┌─ LSP Client ─┐     ┌─────── Agent ────────┐    ┌─ LSP Server ─┐
       │              │     │   ┌──────────────┐   │    │              │
       │        stdout│─────│───│              │───│────│stdin         │
       │              │     │   │ Agent Server │   │    │              │
       │         stdin│─────│───│              │───│────│stdout        │
       │              │     │   └──────────────┘   │    │              │
       │              │     │          │           │    │              │
       └──────────────┘     └──────────┴───────────┘    └──────────────┘
                                       │
                                       │ web socket
                                       │
                                ┌──────────────┐
                                │              │
                                │ Agent Client │
                                │              │
                                └──────────────┘

""",
    )

    cmd.add_argument(
        "--host",
        help="the host to run the websocket server on.",
        default="localhost",
    )
    cmd.add_argument(
        "-p",
        "--port",
        help="the port to run the websocket server on",
        default=8765,
    )

    cmd.set_defaults(run=run_agent)
