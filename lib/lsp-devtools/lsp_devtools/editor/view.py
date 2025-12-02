from __future__ import annotations

import typing

from textual.containers import Container
from textual.widgets import TextArea

if typing.TYPE_CHECKING:
    from textual.app import ComposeResult


class TextEditorView(Container):
    """A view containing a text editor"""

    def compose(self) -> ComposeResult:
        text_area = TextArea()
        text_area.show_line_numbers = True
        yield text_area
