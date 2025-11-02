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

        resource = resources.files("lsp_devtools.handlers").joinpath("dbinit.sql")
        sql_script = resource.read_text(encoding="utf8")

        with closing(sqlite3.connect(self.dbpath)) as conn:
            conn.executescript(sql_script)

    def handle(self, message: JsonRPCMessage):
        with closing(sqlite3.connect(self.dbpath)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO messages VALUES (?, ?, ?)",
                (
                    json.dumps(message.metadata, default=to_json),
                    json.dumps(message.headers, default=to_json),
                    json.dumps(message.body, default=to_json),
                ),
            )

            conn.commit()

    @contextmanager
    def cursor(self, commit: bool = True):
        """Get a connection to the database"""

        db = sqlite3.connect(self.dbpath)
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
