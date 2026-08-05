from __future__ import annotations

from datetime import datetime
from datetime import timezone

import pytest
from textual.app import App
from textual.app import ComposeResult
from textual.widgets import DataTable

from lsp_devtools.handlers.jsonrpc import JsonRPCMessage
from lsp_devtools.handlers.sql import SqlHandler
from lsp_devtools.inspector.message_browser import MessageBrowser


def _message(method: str, msg_id: int) -> JsonRPCMessage:
    message = JsonRPCMessage.client(
        {
            "jsonrpc": "2.0",
            "id": msg_id,
            "method": method,
            "params": {},
        }
    )
    message.metadata["timestamp"] = datetime.now(timezone.utc)
    return message


class BrowserApp(App[None]):
    def __init__(self, db: SqlHandler, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = db

    def compose(self) -> ComposeResult:
        yield MessageBrowser()


@pytest.mark.asyncio
async def test_reload_preserves_selection_when_not_following():
    """New messages must not steal the selected row when follow=False (#247)."""
    db = SqlHandler(":memory:")
    for i in range(3):
        db.handle(_message(f"method/{i}", i))

    app = BrowserApp(db)
    async with app.run_test() as pilot:
        browser = app.query_one(MessageBrowser)
        table = browser.query_one(DataTable)

        browser.reload()
        await pilot.pause()
        assert table.row_count == 3

        table.move_cursor(row=1, animate=False)
        await pilot.pause()
        selected = table.coordinate_to_cell_key(table.cursor_coordinate).row_key

        db.handle(_message("method/new", 99))
        browser.reload(follow=False)
        await pilot.pause()

        assert table.row_count == 4
        assert table.coordinate_to_cell_key(table.cursor_coordinate).row_key == selected
        assert table.cursor_row == 1


@pytest.mark.asyncio
async def test_reload_follows_tail_when_requested():
    """follow=True should select the newest message."""
    db = SqlHandler(":memory:")
    for i in range(2):
        db.handle(_message(f"method/{i}", i))

    app = BrowserApp(db)
    async with app.run_test() as pilot:
        browser = app.query_one(MessageBrowser)
        table = browser.query_one(DataTable)

        browser.reload()
        await pilot.pause()
        table.move_cursor(row=0, animate=False)
        await pilot.pause()

        db.handle(_message("method/new", 99))
        browser.reload(follow=True)
        await pilot.pause()

        assert table.cursor_row == table.row_count - 1


@pytest.mark.asyncio
async def test_is_following_tail():
    db = SqlHandler(":memory:")
    for i in range(3):
        db.handle(_message(f"method/{i}", i))

    app = BrowserApp(db)
    async with app.run_test() as pilot:
        browser = app.query_one(MessageBrowser)
        table = browser.query_one(DataTable)

        browser.reload()
        await pilot.pause()

        table.move_cursor(row=table.row_count - 1, animate=False)
        await pilot.pause()
        assert browser.is_following_tail() is True

        table.move_cursor(row=0, animate=False)
        await pilot.pause()
        assert browser.is_following_tail() is False
