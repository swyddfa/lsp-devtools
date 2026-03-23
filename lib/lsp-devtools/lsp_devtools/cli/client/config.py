from __future__ import annotations

import shlex
import typing

import attrs
from textual.containers import Grid
from textual.containers import Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button
from textual.widgets import Input
from textual.widgets import Label
from textual.widgets import TabbedContent
from textual.widgets import TabPane

if typing.TYPE_CHECKING:
    from textual.app import ComposeResult


@attrs.define
class ServerConfig:
    """Configuration for the server process."""

    command: list[str] = attrs.field(factory=list)


@attrs.define
class AppConfig:
    """Represents the configuration for the whole application."""

    server: ServerConfig = attrs.field(factory=ServerConfig)


class ConfigurationScreen(ModalScreen[AppConfig | None]):
    """A a screen used for configuration settings."""

    DEFAULT_CSS = """
    ConfigurationScreen {
       align: center middle;
    }

    #config-content {
       width: 80%;
       height: auto;
       max-height: 80%;

       background: $panel;
       border: round $primary;

       padding: 2;
       grid-size: 1;
       grid-gutter: 1;
       grid-rows: auto 1fr;
    }

    #config-actions {
      align: right bottom;
      column-span: 2;
    }
    """

    def __init__(self, *args, config: AppConfig, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config

    def compose(self) -> ComposeResult:
        with Grid(id="config-content") as content:
            content.border_title = "Configuration Settings"

            with TabbedContent():
                yield ServerConfigForm(title="Server", config=self.config.server)
                yield ClientConfigForm(title="Client")

            with Horizontal(id="config-actions"):
                yield Button("Cancel", flat=True, id="cancel")
                yield Button("Save", id="save", flat=True, variant="success")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "save":
            server_form = self.query_one(ServerConfigForm)
            config = AppConfig(server=server_form.get_config())
            _ = self.dismiss(config)

            return

        _ = self.dismiss(None)


class ServerConfigForm(TabPane):
    DEFAULT_CSS = """
      #server-settings {
        width: 100%;
        height: auto;

        padding: 2;
        grid-size: 2;
        grid-gutter: 1;
        grid-columns: auto 1fr;
      }
    """

    def __init__(self, *args, config: ServerConfig, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config

    def get_config(self) -> ServerConfig:
        """Return the configuration as defined by the form"""
        command_field = self.query_one("#server-command", Input)
        command = shlex.split(command_field.value)

        return ServerConfig(command=command)

    def set_config(self, config: ServerConfig):
        """Set the form according to the given config."""
        command_field = self.query_one("#server-command#", Input)
        command_field.value = " ".join(config.command)

    def compose(self) -> ComposeResult:
        with Grid(id="server-settings"):
            yield Label("Command")

            command = None
            if len(self.config.command) > 0:
                command = " ".join(self.config.command)

            yield Input(id="server-command", value=command)


class ClientConfigForm(TabPane): ...
