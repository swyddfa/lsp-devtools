from __future__ import annotations

import typing
from datetime import datetime

from textual.containers import Container
from textual.containers import Horizontal
from textual.widgets import Button
from textual.widgets import DataTable
from textual.widgets import TabbedContent
from textual.widgets import TabPane

from lsp_devtools.record.formatters import format_message_source
from lsp_devtools.viewers import RawViewer

if typing.TYPE_CHECKING:
    from textual.widgets.data_table import RowKey

    from lsp_devtools.handlers.jsonrpc import JsonRPCMessage

    from . import LSPInspector


class MessageDetails(Container):
    """A component for viewing a single message in detail"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def compose(self):
        with TabbedContent():
            yield RawViewer(id="raw-viewer")

    def set_message(self, message: JsonRPCMessage):
        container = self.query_one(TabbedContent)

        for tab in container.query(TabPane):
            # TODO: How to get this to typecheck?
            #
            # I can define a MessageViewer protocol, but I don't seem to be able to say
            # "a MessageViewer is also a TabPane"
            if tab.supports_message(message):
                tab.set_message(message)
                container.show_tab(tab.id)
            else:
                container.hide_tab(tab.id)


class MessageBrowser(Container):
    """A component for browsing captured messages."""

    app: LSPInspector

    # fmt: off
    DEFAULT_CSS = Container.DEFAULT_CSS + """

      MessageBrowser {
        layout: grid;
        grid-size: 1 3;
        grid-rows: 3 1fr 1fr;
      }

      DataTable {
        height: 100%;
        width: 100%;
      }

      MessageDetails {
        padding: 1 0;
      }
    """
    # fmt: on

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._messages: dict[RowKey, JsonRPCMessage] = {}

    def compose(self):
        with Horizontal(id="button-row"):
            yield Button(label="X", flat=True, variant="error", compact=True)
            yield Button(label="Filters", flat=True)

        table = DataTable(cursor_type="row")
        table.add_column("Time")
        table.add_column("Source")
        table.add_column("ID")
        table.add_column("Method")
        yield table

        details = MessageDetails()
        yield details

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted):
        if (message := self._messages.get(event.row_key)) is None:
            return

        details = self.query_one(MessageDetails)
        details.set_message(message)

    def reload(self):
        """Reload messages."""
        table = self.query_one(DataTable)
        self._messages.clear()

        for message in self.app.db.find_messages():
            source = ""
            if (msg_source := message.source) is not None:
                source = format_message_source(msg_source)

            timestamp = message.timestamp or datetime.now()
            key = table.add_row(
                f"{timestamp:%H:%M:%S.%f}", source, message.msg_id, message.method
            )
            self._messages[key] = message
