from __future__ import annotations

import json
import pathlib
import sqlite3
from contextlib import closing
from datetime import datetime
from importlib import resources

from .jsonrpc import JsonRPCHandler
from .jsonrpc import JsonRPCMessage


class SqlHandler(JsonRPCHandler):
    """A handler that sends messages to a SQL database"""

    def __init__(self, dbpath: pathlib.Path, *args, **kwargs):
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


def to_json(o):
    """Convert unserializable types to a JSON compatible representation"""

    if isinstance(o, datetime):
        return o.isoformat(" ")

    raise ValueError(f"Unknown type {o.__class__.__name__!r}")
