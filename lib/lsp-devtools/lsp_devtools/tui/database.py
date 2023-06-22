import json
import pathlib
import sys
from contextlib import asynccontextmanager
from typing import Optional

import aiosqlite
from textual import log
from textual.message import Message

from lsp_devtools.handlers import LspMessage

if sys.version_info.minor < 9:
    import importlib_resources as resources
else:
    import importlib.resources as resources  # type: ignore[no-redef]


class PingMessage(Message):
    """Sent when there are updates in the db."""


class Database:
    """Controls access to the backing sqlite database."""

    def __init__(self, dbpath: Optional[pathlib.Path] = None, app=None):
        self.dbpath = dbpath or ":memory:"
        self.db: Optional[aiosqlite.Connection] = None
        self.app = app

    async def close(self):
        if self.db:
            await self.db.close()

    @asynccontextmanager
    async def cursor(self):
        """Get a connection to the database."""

        if self.db is None:
            if (
                isinstance(self.dbpath, pathlib.Path)
                and not self.dbpath.parent.exists()
            ):
                self.dbpath.parent.mkdir(parents=True)

            resource = resources.files("lsp_devtools.handlers").joinpath("dbinit.sql")
            schema = resource.read_text(encoding="utf8")

            self.db = await aiosqlite.connect(self.dbpath)
            await self.db.executescript(schema)
            await self.db.commit()

        cursor = await self.db.cursor()
        yield cursor

        await self.db.commit()

    async def add_message(self, session: str, timestamp: float, source: str, rpc: dict):
        """Add a new rpc message to the database."""

        msg_id = rpc.get("id", None)
        method = rpc.get("method", None)
        params = rpc.get("params", None)
        result = rpc.get("result", None)
        error = rpc.get("error", None)

        async with self.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO protocol VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    session,
                    timestamp,
                    source,
                    msg_id,
                    method,
                    json.dumps(params) if params else None,
                    json.dumps(result) if result else None,
                    json.dumps(error) if error else None,
                ),
            )

        if self.app is not None:
            self.app.post_message(PingMessage())

    async def get_messages(self, max_row=-1):
        """Get messages from the databse"""

        query = "SELECT * FROM protocol WHERE rowid > ?"

        async with self.cursor() as cursor:
            await cursor.execute(query, (max_row,))

            rows = await cursor.fetchall()
            results = []
            for row in rows:
                results.append(
                    LspMessage(
                        session=row[0],
                        timestamp=row[1],
                        source=row[2],
                        id=row[3],
                        method=row[4],
                        params=row[5],
                        result=row[6],
                        error=row[7],
                    )
                )

            return results
