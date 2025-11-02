from __future__ import annotations

import typing
from datetime import datetime

from textual.widgets import DataTable

from lsp_devtools.record.formatters import format_message_source

if typing.TYPE_CHECKING:
    from . import LSPInspector


class MessageTable(DataTable):
    """A data table built for showcasing captured lsp messages."""

    app: LSPInspector

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_column("Time")
        self.add_column("Source")
        self.add_column("ID")
        self.add_column("Method")

        self.cursor_type = "row"

    def reload(self):
        """Reload messages."""

        for message in self.app.db.find_messages():
            source = ""
            if (msg_source := message.source) is not None:
                source = format_message_source(msg_source)

            timestamp = message.timestamp or datetime.now()
            self.add_row(
                f"{timestamp:%H:%M:%S.%f}", source, message.msg_id, message.method
            )
