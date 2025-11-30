from __future__ import annotations

import typing
from datetime import datetime

from textual.containers import Container
from textual.containers import Horizontal
from textual.widgets import Button
from textual.widgets import DataTable
from textual.widgets import TabbedContent
from textual.widgets import TabPane

from lsp_devtools.record.filters import JsonRPCFilter
from lsp_devtools.record.formatters import format_message_source
from lsp_devtools.viewers import RawViewer

from .message_filters import MessageFilters

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
        self._filter = JsonRPCFilter()
        self._last_rowid = -1

    def compose(self):
        with Horizontal(id="button-row"):
            yield Button(label="X", flat=True, variant="error", compact=True)
            yield Button(label="Filters", flat=True, id="set-filters")

        table = DataTable(cursor_type="row")
        table.add_column("Time")
        table.add_column("Source")
        table.add_column("ID")
        table.add_column("Method")
        yield table

        details = MessageDetails()
        yield details

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "set-filters":

            def maybe_set_filter(new_filter: JsonRPCFilter | None):
                if new_filter is not None:
                    self._filter = new_filter
                    self.reload()

            method_names = self.app.db.get_method_names()
            filter_dialog = MessageFilters(
                msg_filter=self._filter, method_names=method_names
            )
            self.app.push_screen(filter_dialog, maybe_set_filter)

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted):
        if (message := self._messages.get(event.row_key)) is None:
            return

        details = self.query_one(MessageDetails)
        details.set_message(message)

    def clear(self):
        """Clear all messages from the table"""

        table = self.query_one(DataTable)
        table.clear()
        self._messages.clear()
        self._last_rowid = -1

    def reload(self, follow: bool = False):
        """Reload messages.

        Parameters
        ----------
        follow
           If ``True``, move the cursor so that the most recent message is selected

        """
        table = self.query_one(DataTable)

        for rowid, message in self.app.db.find_messages(after=self._last_rowid):
            # TODO: Convert the filter into a SQL query so we can take advantage of
            # the fact we're using SQLite!
            if not self._filter.match(message):
                continue

            source = ""
            if (msg_source := message.source) is not None:
                source = format_message_source(msg_source)

            timestamp = message.timestamp or datetime.now()
            key = table.add_row(
                f"{timestamp:%H:%M:%S.%f}",
                source,
                message.msg_id,
                message.method,
                key=str(rowid),
            )
            self._messages[key] = message
            self._last_rowid = rowid

        if follow:
            table.action_scroll_bottom()
