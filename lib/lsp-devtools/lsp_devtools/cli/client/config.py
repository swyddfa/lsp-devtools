from __future__ import annotations

from textual.screen import ModalScreen
from textual.widgets import TabbedContent
from textual.widgets import TabPane


class ConfigurationScreen(ModalScreen[None]):
    """A a screen used for configuration settings."""

    def compose(self):
        with TabbedContent():
            yield ServerConfig(title="Server Settings")
            yield ClientConfig(title="Client Settings")


class ServerConfig(TabPane): ...


class ClientConfig(TabPane): ...
