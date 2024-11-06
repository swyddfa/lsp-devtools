from __future__ import annotations

import argparse
import asyncio
import subprocess
import sys

from .agent import Agent
from .agent import RPCMessage
from .agent import logger
from .agent import parse_rpc_message
from .client import AgentClient
from .server import AgentServer

__all__ = [
    "Agent",
    "AgentClient",
    "AgentServer",
    "RPCMessage",
    "logger",
    "parse_rpc_message",
]


async def forward_stderr(server: asyncio.subprocess.Process):
    """Forward the server's stderr to the agent's stderr."""
    if server.stderr is None:
        return

    # EOF is signalled with an empty bytestring
    while (line := await server.stderr.readline()) != b"":
        sys.stderr.buffer.write(line)


async def main(args, extra: list[str]):
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
    client = AgentClient()
    agent = Agent(server, sys.stdin.buffer, sys.stdout.buffer, client.forward_message)

    await asyncio.gather(
        client.start_tcp(args.host, args.port),
        agent.start(),
        forward_stderr(server),
    )


def run_agent(args, extra: list[str]):
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
