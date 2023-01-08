import json
import pathlib
import sqlite3
import sys
from contextlib import closing

from lsp_devtools.handlers import LspHandler
from lsp_devtools.handlers import LspMessage

if sys.version_info.minor < 9:
    import importlib_resources as resources
else:
    import importlib.resources as resources  # type: ignore[no-redef]


class SqlHandler(LspHandler):
    """A logging handler that sends log records to a SQL database"""

    def __init__(self, dbpath: pathlib.Path, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.dbpath = dbpath

        resource = resources.files("lsp_devtools.handlers").joinpath("dbinit.sql")
        sql_script = resource.read_text(encoding="utf8")

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
