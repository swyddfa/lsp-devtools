import argparse
import asyncio
import json
import logging
import os
import pathlib
import subprocess
import sys
import threading
from typing import BinaryIO
from typing import List

import appdirs
from pygls.protocol import JsonRPCProtocol
from pygls.server import Server

from lsp_devtools.handlers.sql import SqlHandler

logger = logging.getLogger(__name__)


class Agent:
    """The Agent sits between a language server and its client, listening to messages
    enabling them to be recorded in a SQLite database::

       +---- LSP Client ---+        +------ Agent ------+        +---- LSP Server ---+
       |                   |        | +---------------+ |        |                   |
       |                out|--------|>|in  Server  out|-|------->|in                 |
       |                   |        | +---------------+ |        |                   |
       |                 in|<-------|-|out Server   in|<|--------|out                |
       |                   |        | +---------------+ |        |                   |
       +-------------------+        +-------------------+        +-------------------+


    """

    def __init__(self, server: subprocess.Popen, stdin: BinaryIO, stdout: BinaryIO):
        self.stdin = stdin
        self.stdout = stdout
        self.server_process = server

    def start(self):
        """Setup the connections between client and server and start it all running."""

        self.client_to_server = Server(protocol_cls=Passthrough)
        self.client_to_server.lsp.source = "client"
        self.client_to_server_thread = threading.Thread(
            name="Client -> Server",
            target=self.client_to_server.start_io,
            args=(self.stdin, self.server_process.stdin),
        )
        self.client_to_server_thread.daemon = True

        self.server_to_client = Server(
            protocol_cls=Passthrough, loop=asyncio.new_event_loop()
        )
        self.server_to_client.lsp.source = "server"
        self.server_to_client_thread = threading.Thread(
            name="Server -> Client",
            target=self.server_to_client.start_io,
            args=(self.server_process.stdout, self.stdout),
        )
        self.server_to_client_thread.daemon = True

        self.client_to_server_thread.start()
        self.server_to_client_thread.start()

    def join(self):
        self.client_to_server_thread.join()
        self.server_to_client_thread.join()


class Passthrough(JsonRPCProtocol):
    """A JsonRPCProtocol implementation that simpy forwards the messages it recevies
    while also logging them."""

    source: str

    def data_received(self, data: bytes):
        """A slightly modified version of the method found in upstream pygls.

        As well as immediately writing the data we receive to the transport, we also
        bypass pygls' message parsing code and log the raw json object.
        """
        logger.debug("Received %r", data)

        while len(data):

            # Forward on the data as we receive it
            self.transport.write(data)
            logger.debug(data.decode(self.CHARSET), extra={"source": self.source})

            # Append the incoming chunk to the message buffer
            self._message_buf.append(data)

            # Look for the body of the message
            message = b"".join(self._message_buf)
            found = JsonRPCProtocol.MESSAGE_PATTERN.fullmatch(message)

            body = found.group("body") if found else b""
            length = int(found.group("length")) if found else 1

            if len(body) < length:
                # Message is incomplete; bail until more data arrives
                return

            # Message is complete;
            # extract the body and any remaining data,
            # and reset the buffer for the next message
            body, data = body[:length], body[length:]
            self._message_buf = []

            # Log the full message
            logger.info(
                "%s",
                json.loads(body.decode(self.CHARSET)),
                extra={"source": self.source},
            )


def agent(args, extra: List[str]):
    """Run the LSP agent."""

    if extra is None:
        print("Missing server start command", file=sys.stderr)
        return 1

    dbpath = pathlib.Path(args.db)
    if not dbpath.parent.exists():
        dbpath.parent.mkdir(parents=True)

    server_process = subprocess.Popen(
        extra, stdin=subprocess.PIPE, stdout=subprocess.PIPE
    )

    logger = logging.getLogger("lsp_devtools.agent")
    logger.setLevel(logging.INFO)

    sql_handler = SqlHandler(dbpath)
    sql_handler.setLevel(logging.INFO)

    logger.addHandler(sql_handler)

    agent = Agent(server_process, sys.stdin.buffer, sys.stdout.buffer)
    agent.start()
    agent.join()


def cli(commands: argparse._SubParsersAction):
    cmd = commands.add_parser(
        "agent",
        help="agent for recording communications between an LSP client and server.",
    )
    cmd.add_argument(
        "--db",
        help="path to use for the database",
        default=os.path.join(
            appdirs.user_data_dir(appname="lsp-devtools"), "lsp_sessions.db"
        ),
    )
    cmd.set_defaults(run=agent)
