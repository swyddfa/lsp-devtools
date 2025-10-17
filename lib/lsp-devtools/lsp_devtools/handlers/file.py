from __future__ import annotations

import typing

from .jsonrpc import JsonRPCHandler
from .jsonrpc import JsonRPCMessage

if typing.TYPE_CHECKING:
    from typing import Protocol
    from typing import TextIO

    class JsonRPCFormatter(Protocol):
        def format(self, message: JsonRPCMessage) -> str | None:
            """Convert a message to a string, maybe."""


class FileHandler(JsonRPCHandler):
    """A JSON-RPC handler that writes messages to a file."""

    def __init__(self, fp: TextIO, formatter: JsonRPCFormatter, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fp: TextIO = fp
        self.formatter: JsonRPCFormatter = formatter

    def handle(self, message: JsonRPCMessage):
        if (line := self.formatter.format(message)) is not None:
            self.fp.write(line + "\n")

    def stop(self):
        self.fp.close()
        super().stop()
