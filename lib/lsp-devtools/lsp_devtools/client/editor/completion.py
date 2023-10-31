from lsprotocol import types
from textual import events
from textual.binding import Binding
from textual.widgets import OptionList


class CompletionList(OptionList):
    BINDINGS = [
        Binding("escape", "dismiss", "Dismiss", show=False),
    ]

    @classmethod
    def fromresult(cls, result):
        """Build a list of completion candidates based on a response from the
        language server."""

        if result is None:
            return None

        if isinstance(result, types.CompletionList):
            items = result.items
        else:
            items = result

        if len(items) == 0:
            return None

        candidates = cls()
        candidates.add_options(
            sorted(
                [CompletionItem(i) for i in items],
                key=lambda i: i.item.label,  # type: ignore
            )
        )
        return candidates

    def on_blur(self, event: events.Blur):
        self.action_dismiss()

    def action_dismiss(self):
        self.remove()
        if self.parent:
            self.app.set_focus(self.parent)  # type: ignore


class CompletionItem:
    """Renders a completion item for display in a completion list."""

    def __init__(self, item: types.CompletionItem):
        self.item = item

    def __rich__(self):
        # TODO: Make pretty
        return self.item.label

    def __getattr__(self, key):
        return getattr(self.item, key)
