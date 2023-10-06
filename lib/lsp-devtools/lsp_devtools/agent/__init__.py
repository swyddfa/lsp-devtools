import argparse
import asyncio
import logging
import subprocess
import sys
from typing import List
from uuid import uuid4

from .agent import Agent
from .agent import logger
from .client import AgentClient
from .protocol import MESSAGE_TEXT_NOTIFICATION
from .protocol import MessageText
from .server import AgentServer
from .server import parse_rpc_message

__all__ = [
    "Agent",
    "AgentClient",
    "AgentServer",
    "logger",
    "MESSAGE_TEXT_NOTIFICATION",
    "MessageText",
    "parse_rpc_message",
]


class MessageHandler(logging.Handler):
    """Logging handler that forwards captured JSON-RPC messages through to the
    ``AgentServer`` instance."""

    def __init__(self, client: AgentClient, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = client
        self.session = str(uuid4())
        self._buffer: List[MessageText] = []

    def emit(self, record: logging.LogRecord):
        message = MessageText(
            text=record.args[0],  # type: ignore
            session=self.session,
            timestamp=record.created,
            source=record.__dict__["source"],
        )

        if not self.client.connected:
            self._buffer.append(message)
            return

        # Send any buffered messages
        while len(self._buffer) > 0:
            self.client.protocol.message_text_notification(self._buffer.pop(0))

        self.client.protocol.message_text_notification(message)


async def main(args, extra: List[str]):
    if extra is None:
        print("Missing server start command", file=sys.stderr)
        return 1

    command, *arguments = extra

    server = await asyncio.create_subprocess_exec(
        command,
        *arguments,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    agent = Agent(server, sys.stdin.buffer, sys.stdout.buffer)

    client = AgentClient()
    handler = MessageHandler(client)
    handler.setLevel(logging.INFO)

    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    await asyncio.gather(
        client.start_tcp(args.host, args.port),
        agent.start(),
    )


def run_agent(args, extra: List[str]):
    asyncio.run(main(args, extra))


def cli(commands: argparse._SubParsersAction):
    cmd: argparse.ArgumentParser = commands.add_parser(
        "agent",
        help="instrument an LSP session",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
This command runs the given JSON-RPC server as a subprocess, wrapping it in a
an "AgentClient" which will capture all messages sent to/from the wrapped
server, forwarding them onto an "AgentServer" to be processed.

To wrap a server, supply its start command after all other agent options and
preceeded by a `--`, for example:

    lsp-devtools agent -p 1234 -- python -m esbonio

Wrapping a JSON-RPC server with this command is required to enable the
majority of the lsp-devtools suite of tools.

       ┌─ RPC Client ─┐     ┌──── Agent Client ────┐    ┌─ RPC Server ─┐
       │              │     │   ┌──────────────┐   │    │              │
       │        stdout│─────│───│              │───│────│stdin         │
       │              │     │   │    Agent     │   │    │              │
       │         stdin│─────│───│              │───│────│stdout        │
       │              │     │   └──────────────┘   │    │              │
       │              │     │                      │    │              │
       └──────────────┘     └──────────────────────┘    └──────────────┘
                                       │
                                       │ tcp/websocket
                                       │
                                ┌──────────────┐
                                │              │
                                │ Agent Server │
                                │              │
                                └──────────────┘

""",
    )

    cmd.add_argument(
        "--host",
        help="the host to connect to.",
        default="localhost",
    )
    cmd.add_argument(
        "-p",
        "--port",
        help="the port to connect to",
        default=8765,
    )

    cmd.set_defaults(run=run_agent)
