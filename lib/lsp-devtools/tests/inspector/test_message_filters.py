from __future__ import annotations

import pytest
from textual.app import App
from textual.widgets import RadioSet
from textual.widgets import SelectionList

from lsp_devtools.inspector.message_filters import MessageFilters
from lsp_devtools.record.filters import JsonRPCFilter


class FilterApp(App):
    BINDINGS = [("f", "set_filters", "Set Filters")]

    def __init__(self, msg_filter: JsonRPCFilter, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.msg_filter = msg_filter
        self.result: JsonRPCFilter | None = None

    def action_set_filters(self):
        def catch(result: JsonRPCFilter | None):
            self.result = result

        self.push_screen(
            MessageFilters(
                self.msg_filter,
                [
                    "initialize",
                    "textDocument/didOpen",
                    "textDocument/didChange",
                    "textDocument/completion",
                ],
            ),
            catch,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "msg_filter, expected",
    [
        (JsonRPCFilter(), "Both"),
        (JsonRPCFilter(message_source="both"), "Both"),
        (JsonRPCFilter(message_source="server"), "Server"),
        (JsonRPCFilter(message_source="client"), "Client"),
    ],
)
async def test_init_form_source(msg_filter: JsonRPCFilter, expected: str):
    """Ensure that the form can populate the message source filter correctly given an
    initial filter."""

    app = FilterApp(msg_filter)

    async with app.run_test() as pilot:
        await pilot.press("f")

        dialog = app.screen_stack[1]
        assert isinstance(dialog, MessageFilters)

        msg_source = dialog.query_one("#msg-source", RadioSet)
        assert str(msg_source.pressed_button.label) == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "msg_filter, expected",
    [
        (JsonRPCFilter(), []),
        (JsonRPCFilter(include_message_types=["error"]), ["error"]),
        (JsonRPCFilter(include_message_types=["request"]), ["request"]),
        (JsonRPCFilter(include_message_types=["result"]), ["result"]),
        (JsonRPCFilter(include_message_types=["response"]), ["response"]),
        (JsonRPCFilter(include_message_types=["notification"]), ["notification"]),
        (
            JsonRPCFilter(include_message_types=["request", "notification"]),
            ["request", "notification"],
        ),
    ],
)
async def test_init_form_type(msg_filter: JsonRPCFilter, expected: list[str]):
    """Ensure that the form can populate the message type filter correctly given an
    initial filter."""

    app = FilterApp(msg_filter)

    async with app.run_test() as pilot:
        await pilot.press("f")

        dialog = app.screen_stack[1]
        assert isinstance(dialog, MessageFilters)

        msg_type = dialog.query_one("#msg-type", SelectionList)
        assert msg_type.selected == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "msg_filter, expected",
    [
        (JsonRPCFilter(), []),
        (JsonRPCFilter(include_methods=["initialize"]), ["initialize"]),
        (
            JsonRPCFilter(
                include_methods=["textDocument/didOpen", "textDocument/didChange"]
            ),
            ["textDocument/didOpen", "textDocument/didChange"],
        ),
    ],
)
async def test_init_form_method(msg_filter: JsonRPCFilter, expected: list[str]):
    """Ensure that the form can populate the method filter correctly given an
    initial filter."""

    app = FilterApp(msg_filter)

    async with app.run_test() as pilot:
        await pilot.press("f")

        dialog = app.screen_stack[1]
        assert isinstance(dialog, MessageFilters)

        included_methods = dialog.query_one("#msg-methods", SelectionList)
        assert included_methods.selected == expected
