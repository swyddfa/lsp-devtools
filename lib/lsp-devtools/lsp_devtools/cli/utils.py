from __future__ import annotations

import logging
import pathlib
import tempfile
import typing

from textual.message import Message

from lsp_devtools.handlers.sql import SqlHandler

if typing.TYPE_CHECKING:
    from typing import Any

    from textual.app import App

    from lsp_devtools.handlers.jsonrpc import JsonRPCMessage

LOG_LEVELS = [logging.WARNING, logging.INFO, logging.DEBUG]


def get_log_level(verbosity: int) -> int:
    """Get the logging level corresponding to the given verbosity"""
    return LOG_LEVELS[min(max(0, verbosity), len(LOG_LEVELS) - 1)]


class LiveSqlHandler(SqlHandler):
    """A SqlHandler with a textual app reference so it can trigger a refresh when
    messages are received."""

    class MessageReceived(Message):
        def __init__(self, message: JsonRPCMessage):
            self.message = message
            super().__init__()

    def __init__(self, dbpath: None | pathlib.Path = None, *args, **kwargs):
        if dbpath is None:
            # In order to have concurrent access to a SQLite db, it must be backed by a file
            # https://sqlite.org/pragma.html#pragma_locking_mode
            self._dbdir = tempfile.TemporaryDirectory()
            dbpath = pathlib.Path(self._dbdir.name, "session.db")

        super().__init__(*args, dbpath=dbpath, **kwargs)
        self.app: App[Any] | None = None

    def __del__(self):
        super().__del__()
        self._dbdir.cleanup()

    def handle(self, message: JsonRPCMessage):
        super().handle(message)

        if self.app is not None:
            self.app.post_message(self.MessageReceived(message))
