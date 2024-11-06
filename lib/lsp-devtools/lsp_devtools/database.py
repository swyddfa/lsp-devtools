import asyncio
import json
import logging
import pathlib
from contextlib import asynccontextmanager
from importlib import resources
from typing import Any
from typing import Optional

import aiosqlite
from textual.app import App
from textual.message import Message

from lsp_devtools.handlers import LspMessage


class Database:
    """Controls access to the backing sqlite database."""

    class Update(Message):
        """Sent when there are updates to the database"""

    def __init__(self, dbpath: Optional[pathlib.Path] = None):
        self.dbpath = dbpath or ":memory:"
        self.db: Optional[aiosqlite.Connection] = None
        self.app: Optional[App] = None
        self._handlers: dict[str, set] = {}

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

    async def add_message(self, session: str, timestamp: str, source: str, rpc: dict):
        """Add a new rpc message to the database."""

        msg_id = rpc.get("id")
        method = rpc.get("method")
        params = rpc.get("params")
        result = rpc.get("result")
        error = rpc.get("error")

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
            self.app.post_message(Database.Update())

    async def get_messages(
        self,
        *,
        session: str = "",
        max_row: Optional[int] = None,
    ):
        """Get messages from the database

        Parameters
        ----------
        session
           If set, only return messages with the given session id

        max_row
           If set, only return messages with a row id greater than ``max_row``
        """

        base_query = "SELECT rowid, * FROM protocol"
        where: list[str] = []
        parameters: list[Any] = []

        if session:
            where.append("session = ?")
            parameters.append(session)

        if max_row:
            where.append("rowid > ?")
            parameters.append(max_row)

        if where:
            conditions = " AND ".join(where)
            query = " ".join([base_query, "WHERE", conditions])
        else:
            query = base_query

        async with self.cursor() as cursor:
            await cursor.execute(query, tuple(parameters))

            rows = await cursor.fetchall()
            results = []
            for row in rows:
                message = LspMessage(
                    session=row[1],
                    timestamp=row[2],
                    source=row[3],
                    id=row[4],
                    method=row[5],
                    params=row[6],
                    result=row[7],
                    error=row[8],
                )

                results.append((row[0], message))

            return results


class DatabaseLogHandler(logging.Handler):
    """A logging handler that records messages in the given database."""

    def __init__(self, db: Database, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = db
        self._tasks: set[asyncio.Task] = set()

    def emit(self, record: logging.LogRecord):
        body = json.loads(record.args[0])  # type: ignore
        task = asyncio.create_task(
            self.db.add_message(
                record.__dict__["Message-Session"],
                record.__dict__["Message-Timestamp"],
                record.__dict__["Message-Source"],
                body,
            )
        )

        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
