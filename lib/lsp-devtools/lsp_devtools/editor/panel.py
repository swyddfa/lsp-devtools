from __future__ import annotations

from textual.containers import Container
from textual.widgets import Log
from textual.widgets import TabbedContent
from textual.widgets import TabPane


class Panel(Container):
    """A panel component, like you might find in VSCode."""

    def compose(self):
        with TabbedContent():
            yield OutputWindow(id="stderr-window", title="Stderr")
            yield OutputWindow(id="log-window", title="Log")


class OutputWindow(TabPane):
    def compose(self):
        yield Log()

    def write(self, data: bytes):
        log = self.query_one(Log)
        log.write(data.decode("utf8"))
