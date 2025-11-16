from __future__ import annotations

import typing

from rich.highlighter import ReprHighlighter
from rich.text import Text
from textual.widgets import DataTable
from textual.widgets import TabPane
from textual.widgets import Tree

if typing.TYPE_CHECKING:
    from typing import Any

    from textual.app import ComposeResult
    from textual.content import ContentType
    from textual.widgets.tree import TreeNode

    from lsp_devtools.handlers.jsonrpc import JsonRPCMessage


class RawViewer(TabPane):
    """Widget for viewing the raw contents of a message."""

    DEFAULT_CSS = """
      RawViewer {
        layout: grid;
        grid-size: 2;
        grid-rows: auto 1fr;
      }

      RawViewer DataTable {
        border: round $primary;
      }

      RawViewer Tree {
        column-span: 2;
        border: round $primary;
      }
    """

    def __init__(self, title: ContentType = "Raw", *args, **kwargs):
        super().__init__(title, *args, **kwargs)
        self.highlighter = ReprHighlighter()

    def compose(self) -> ComposeResult:
        table = DataTable(cursor_type="row", id="msg-headers")
        table.add_column("Name")
        table.add_column("Value")
        table.border_subtitle = "Headers"

        yield table

        table = DataTable(cursor_type="row", id="msg-metadata")
        table.add_column("Name")
        table.add_column("Value")
        table.border_subtitle = "Metadata"

        yield table

        content = Tree(label="payload")
        content.border_subtitle = "Payload"
        yield content

    def supports_message(self, message: JsonRPCMessage) -> bool:
        """Returns ``True`` if this viewer supports the give message"""
        return True

    def set_message(self, message: JsonRPCMessage):
        table: DataTable = self.query_one("#msg-headers")
        table.clear()

        for key, value in message.headers.items():
            table.add_row(key, value)

        table: DataTable = self.query_one("#msg-metadata")
        table.clear()

        for key, value in message.metadata.items():
            table.add_row(key, value)

        tree = self.query_one(Tree)
        tree.clear()
        tree.show_root = False
        self.walk_object("payload", tree.root, message.body)

    def walk_object(self, label: str, node: TreeNode[Any], obj: Any):
        if isinstance(obj, dict):
            node.expand()
            for field, value in obj.items():
                child = node.add(field)
                self.walk_object(field, child, value)

        elif isinstance(obj, list):
            node.expand()
            for idx, value in enumerate(obj):
                child_label = self.highlighter(str(idx))
                child = node.add(child_label)
                self.walk_object(str(idx), child, value)

        else:
            node.allow_expand = False
            node.set_label(Text.assemble(label, " = ", self.highlighter(repr(obj))))
