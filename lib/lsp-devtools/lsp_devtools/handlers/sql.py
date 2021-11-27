import json
import pathlib
import sqlite3

from contextlib import closing

import pkg_resources

from lsp_devtools.handlers import LspHandler
from lsp_devtools.handlers import LspMessage


class SqlHandler(LspHandler):
    """A logging handler that sends log records to a SQL database"""

    def __init__(self, dbpath: pathlib.Path, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.dbpath = dbpath

        resource = pkg_resources.resource_string(__name__, "dbinit.sql")
        sql_script = resource.decode("utf8")

        with closing(sqlite3.connect(self.dbpath)) as conn:
            conn.executescript(sql_script)

    def handle_message(self, message: LspMessage):

        with closing(sqlite3.connect(self.dbpath)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO protocol VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    message.session,
                    message.timestamp,
                    message.source,
                    message.id,
                    message.method,
                    json.dumps(message.params) if message.params else None,
                    json.dumps(message.result) if message.result else None,
                    json.dumps(message.error) if message.error else None,
                ),
            )

            conn.commit()
