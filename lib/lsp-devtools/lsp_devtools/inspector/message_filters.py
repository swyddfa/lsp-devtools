from __future__ import annotations

from textual.containers import Grid
from textual.containers import Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button
from textual.widgets import RadioButton
from textual.widgets import RadioSet
from textual.widgets import SelectionList

from lsp_devtools.agent import MessageSource
from lsp_devtools.record.filters import JsonRPCFilter


class MessageFilters(ModalScreen[JsonRPCFilter | None]):
    """A screen for configuring the filters to use.

    Parameters
    ----------
    msg_filter
       The existing filter configuration

    method_names
       The list of all known JSON-RPC method names
    """

    DEFAULT_CSS = """
    MessageFilters {
       align: center middle;
    }

    #filter-content {
       width: 80%;
       height: auto;
       max-height: 80%;

       background: $panel;
       border: round $primary;

       padding: 2;
       grid-size: 2;
       grid-gutter: 1;
       grid-rows: auto auto 1fr;
    }

    #filter-actions {
      align: right bottom;
      column-span: 2;
    }

    #msg-type {
       border: tall $primary;
    }

    #msg-methods {
       border: tall $primary;
       column-span: 2;
    }
    """

    def __init__(
        self, msg_filter: JsonRPCFilter, method_names: list[str], *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.method_names = method_names
        self.msg_filter = JsonRPCFilter(
            message_source=msg_filter.message_source,
            include_message_types=msg_filter.include_message_types,
            include_methods=msg_filter.include_methods,
        )

    def compose(self):
        with Grid(id="filter-content") as content:
            content.border_title = "Set Filters"

            with RadioSet(id="msg-source") as msg_source:
                msg_source.border_subtitle = "Message Source"
                yield RadioButton(
                    "Both", value=self.msg_filter.message_source == "both"
                )
                yield RadioButton(
                    "Client",
                    value=self.msg_filter.message_source == MessageSource.CLIENT,
                )
                yield RadioButton(
                    "Server",
                    value=self.msg_filter.message_source == MessageSource.SERVER,
                )

            selected_types = [
                (
                    msg_type,
                    msg_type.lower(),
                    msg_type.lower() in self.msg_filter.include_message_types,
                )
                for msg_type in (
                    "Error",
                    "Request",
                    "Response",
                    "Result",
                    "Notification",
                )
            ]
            msg_types = SelectionList(*selected_types, id="msg-type")
            msg_types.border_subtitle = "Message Types"
            yield msg_types

            selected_methods = [
                (method, method, method in self.msg_filter.include_methods)
                for method in self.method_names
            ]
            msg_methods = SelectionList(*selected_methods, id="msg-methods")
            msg_methods.border_subtitle = "Method Names"
            yield msg_methods

            with Horizontal(id="filter-actions"):
                yield Button("Cancel", flat=True, id="cancel")
                yield Button("Save", id="save", flat=True, variant="success")

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Record filter values based on radio button selections"""
        if event.radio_set.id == "msg-source":
            label = event.pressed.label
            self.msg_filter.message_source = str(label).lower()

    def on_selection_list_selected_changed(
        self, event: SelectionList.SelectedChanged[str]
    ):
        """Update filter values based selection lists selections"""
        if event.selection_list.id == "msg-type":
            self.msg_filter.include_message_types = event.selection_list.selected

        if event.selection_list.id == "msg-methods":
            self.msg_filter.include_methods = event.selection_list.selected

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "save":
            self.dismiss(self.msg_filter)

        self.dismiss(None)
