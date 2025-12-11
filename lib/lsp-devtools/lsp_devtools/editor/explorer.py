from __future__ import annotations

import typing

from textual.containers import Container
from textual.widgets import DirectoryTree

if typing.TYPE_CHECKING:
    from textual.app import ComposeResult


class Explorer(Container):
    def compose(self) -> ComposeResult:
        yield DirectoryTree(".")
