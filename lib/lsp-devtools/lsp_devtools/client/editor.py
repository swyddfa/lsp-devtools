import asyncio
import pathlib
from typing import Optional
from typing import Set

from lsprotocol import types
from pygls import uris as uri
from pygls.capabilities import get_capability
from textual import events
from textual import log
from textual import on
from textual.binding import Binding
from textual.widgets import OptionList
from textual.widgets import TextArea

from .lsp import LanguageClient


class CompletionList(OptionList):
    BINDINGS = [
        Binding("escape", "dismiss", "Dismiss", show=False),
        Binding("ctrl+j", "dismiss", "Dismiss", show=False),
    ]

    @classmethod
    def fromresult(cls, result):
        """Build a list of completion candidates based on a response from the
        language server."""
        candidates = cls()

        if result is None:
            return candidates

        if isinstance(result, types.CompletionList):
            items = result.items
        else:
            items = result

        if len(items) == 0:
            return candidates

        candidates.add_options(sorted([i.label for i in items]))
        return candidates

    def on_blur(self, event: events.Blur):
        self.action_dismiss()

    def action_dismiss(self):
        self.remove()
        if self.parent:
            self.app.set_focus(self.parent)


class TextEditor(TextArea):
    def __init__(self, lsp_client: LanguageClient, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.uri = None
        self.version = 0

        self.lsp_client = lsp_client
        self.capabilities: Optional[types.ServerCapabilities] = None

        self._tasks: Set[asyncio.Task] = set()

    @property
    def completion_triggers(self):
        return get_capability(
            self.capabilities, "completion_provider.trigger_characters", set()
        )

    def open_file(self, path: pathlib.Path):
        self.uri = uri.from_fs_path(str(path.resolve()))
        if self.uri is None:
            return

        content = path.read_text()
        self.version = 0
        self.load_text(content)

        self.lsp_client.text_document_did_open(
            types.DidOpenTextDocumentParams(
                text_document=types.TextDocumentItem(
                    uri=self.uri,
                    language_id="restructuredtext",
                    version=self.version,
                    text=content,
                )
            )
        )

    def edit(self, edit):
        super().edit(edit)

        if self.uri is None:
            return

        self.version += 1
        start_line, start_col = edit.from_location
        end_line, end_col = edit.to_location

        self.lsp_client.text_document_did_change(
            types.DidChangeTextDocumentParams(
                text_document=types.VersionedTextDocumentIdentifier(
                    version=self.version, uri=self.uri
                ),
                content_changes=[
                    types.TextDocumentContentChangeEvent_Type1(
                        text=edit.text,
                        range=types.Range(
                            start=types.Position(line=start_line, character=start_col),
                            end=types.Position(line=end_line, character=end_col),
                        ),
                    )
                ],
            )
        )

        if len(edit.text) == 0:
            return

        char = edit.text[-1]
        if char in self.completion_triggers:
            self.trigger_completion(end_line, end_col)

    def trigger_completion(self, line: int, character: int):
        """Trigger completion at the given location."""
        task = asyncio.create_task(
            self.lsp_client.text_document_completion_async(
                types.CompletionParams(
                    text_document=types.TextDocumentIdentifier(uri=self.uri),
                    position=types.Position(line=line, character=character),
                )
            )
        )

        self._tasks.add(task)
        task.add_done_callback(self.show_completions)

    def show_completions(self, task: asyncio.Task):
        self._tasks.discard(task)

        candidates = CompletionList.fromresult(task.result())
        if candidates.option_count == 0:
            return

        row, col = self.cursor_location
        candidates.offset = (col + 2, row + 1)

        self.mount(candidates)
        self.app.set_focus(candidates)

    @on(OptionList.OptionSelected)
    def completion_selected(self, event: OptionList.OptionSelected):
        log(f"{event.option} was selected!")
        event.option_list.action_dismiss()
