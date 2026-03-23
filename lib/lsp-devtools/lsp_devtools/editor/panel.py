from __future__ import annotations

import logging
import typing

from textual.containers import Container
from textual.widgets import RichLog
from textual.widgets import TabbedContent
from textual.widgets import TabPane


class Panel(Container):
    """A panel component, like you might find in VSCode."""

    def compose(self):
        with TabbedContent():
            yield OutputWindow(id="stderr-window", title="Server")
            yield OutputWindow(id="log-window", title="window/logMessage")


@typing.final
class OutputWindowHandler(logging.Handler):
    """A logging handler that writes into an output window."""

    def __init__(self, output: OutputWindow, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.output = output

    def emit(self, record: logging.LogRecord) -> None:
        message = self.format(record)

        if record.levelno == logging.DEBUG:
            message = f"[dim]{message}[/dim]"
        elif record.levelno == logging.ERROR:
            message = f"[bold red]{message}[/bold red]"

        return self.output.write(message)


@typing.final
class OutputWindow(TabPane):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log_handler = OutputWindowHandler(self)

    def compose(self):
        yield RichLog(markup=True)

    def clear(self):
        log = self.query_one(RichLog)
        log.clear()

    def write(self, text: str):
        log = self.query_one(RichLog)
        _ = log.write(text)
