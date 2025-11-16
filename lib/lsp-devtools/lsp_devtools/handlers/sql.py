from __future__ import annotations

import json
import pathlib
import sqlite3
import typing
from contextlib import closing
from contextlib import contextmanager
from datetime import datetime
from importlib import resources

from .jsonrpc import JsonRPCHandler
from .jsonrpc import JsonRPCMessage

if typing.TYPE_CHECKING:
    from typing import Literal


class SqlHandler(JsonRPCHandler):
    """A handler that sends messages to a SQL database"""

    def __init__(self, dbpath: pathlib.Path | Literal[":memory:"], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dbpath = dbpath

        self._mem_db: sqlite3.Connection | None = self._init_db()

    def _init_db(self):
        resource = resources.files("lsp_devtools.handlers").joinpath("dbinit.sql")
        sql_script = resource.read_text(encoding="utf8")

        conn = None
        if self.dbpath == ":memory:":
            # Create a persistent connection to keep the data alive.
            conn = sqlite3.connect(self.connection_string, uri=True)

        with self.cursor() as cursor:
            cursor.executescript(sql_script)

        return conn

    def __del__(self):
        # Clean up data when this is destroyed
        if self._mem_db is not None:
            self._mem_db.close()

    def handle(self, message: JsonRPCMessage):
        with self.cursor() as cursor:
            cursor.execute(
                "INSERT INTO messages VALUES (?, ?, ?)",
                (
                    json.dumps(message.metadata, default=to_json),
                    json.dumps(message.headers, default=to_json),
                    json.dumps(message.body, default=to_json),
                ),
            )

    @property
    def connection_string(self) -> str:
        """Return the string to use when connecting to the db"""
        # See "In-memory Databases and Shared Cache"
        # https://www.sqlite.org/inmemorydb.html
        if self.dbpath == ":memory:":
            uri = f"file:{id(self)}?mode=memory&cache=shared"
            return uri

        return self.dbpath.resolve().as_uri()

    @contextmanager
    def cursor(self, commit: bool = True):
        """Get a connection to the database"""

        with closing(sqlite3.connect(self.connection_string, uri=True)) as db:
            cursor = db.cursor()

            yield cursor

            if commit:
                db.commit()

    def find_messages(self):
        with self.cursor() as db:
            rows = db.execute("select * from messages")
            for row in rows:
                message = JsonRPCMessage(
                    metadata=json.loads(row[0]),
                    headers=json.loads(row[1]),
                    body=json.loads(row[2]),
                )
                yield message


def to_json(o):
    """Convert unserializable types to a JSON compatible representation"""

    if isinstance(o, datetime):
        return o.isoformat(" ")

    raise ValueError(f"Unknown type {o.__class__.__name__!r}")
