import asyncio
import io
import json
import logging
import pathlib
import sqlite3
import subprocess
import threading
import uuid

from contextlib import closing

import pkg_resources

from pygls.protocol import JsonRPCProtocol
from pygls.server import Server

logger = logging.getLogger("agent")


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
            logger.info("%s", json.loads(body.decode(self.CHARSET)), extra={"source": self.source})


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

    def __init__(self, server: subprocess.Popen, stdin: io.BytesIO, stdout: io.BytesIO):
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


class SqlHandler(logging.Handler):
    """A logging handler that sends log records to a SQL database"""

    def __init__(self, dbpath: pathlib.Path, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.dbpath = dbpath
        self.session_id = None

        resource = pkg_resources.resource_string(__name__, "dbinit.sql")
        sql_script = resource.decode("utf8")

        with closing(sqlite3.connect(self.dbpath)) as conn:
            conn.executescript(sql_script)

    def emit(self, record: logging.LogRecord):
        """Send log records to the database."""

        message = record.args
        timestamp = record.created
        source = record.__dict__["source"]

        # message = json.loads(msg)
        id_ = message.get("id", None)
        method = message.get("method", None)

        # Do we need to generate a new session id?
        if method == "initialize":
            self.session_id = str(uuid.uuid4())

        params = None
        if "params" in message:
            params = json.dumps(message["params"])

        result = None
        if "result" in message:
            result = json.dumps(message["result"])

        error = None
        if "error" in message:
            error = json.dumps(message["error"])

        with closing(sqlite3.connect(self.dbpath)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO protocol VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    self.session_id,
                    timestamp,
                    source,
                    id_,
                    method,
                    params,
                    result,
                    error,
                ),
            )

            conn.commit()
