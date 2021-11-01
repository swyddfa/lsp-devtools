import json 
import logging 
import pathlib
import sqlite3
import uuid

from contextlib import closing

import pkg_resources

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
