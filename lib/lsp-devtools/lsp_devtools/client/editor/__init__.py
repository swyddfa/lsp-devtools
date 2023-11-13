from __future__ import annotations

import pathlib
import typing

from lsprotocol import types
from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import OptionList

from .completion import CompletionList
from .text_editor import TextEditor

if typing.TYPE_CHECKING:
    from lsp_devtools.client.lsp import LanguageClient


class EditorView(Vertical):
    """A container to manage all the widgets that make up a single text editor."""

    def __init__(self, lsp_client: LanguageClient, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lsp_client = lsp_client

    def compose(self) -> ComposeResult:
        yield TextEditor(self.lsp_client)

    def open_file(self, path: pathlib.Path):
        editor = self.query_one(TextEditor)
        editor.open_file(path)
        editor.focus()

    def on_text_editor_completion(self, completion: TextEditor.Completion):
        """Render textDocument/completion results."""
        candidates = CompletionList.fromresult(completion.result)
        if candidates is None:
            return

        editor = self.query_one(TextEditor)
        row, col = editor.cursor_location

        gutter_width = 2  # TODO: How to get actual gutter width?
        first_line = 0  # TODO: How to get the first visible line number?
        candidates.offset = (col + gutter_width, row - first_line + 1)

        self.mount(candidates)
        self.app.set_focus(candidates)

    @on(OptionList.OptionSelected)
    def insert_selected_completion(self, event: CompletionList.OptionSelected):
        """Insert the completion item selected by the user into the editor."""
        selected: types.CompletionItem = event.option.prompt  # type: ignore
        event.option_list.action_dismiss()  # type: ignore

        editor = self.query_one(TextEditor)
        if (edit := selected.text_edit) is not None:
            # TODO: Support InsertReplaceEdit
            if isinstance(edit, types.InsertReplaceEdit):
                return

            # TextEdit support.
            start = edit.range.start.line, edit.range.start.character
            end = edit.range.end.line, edit.range.end.character

            with editor.set_state(suppress_completion=True):
                editor.replace(
                    edit.new_text, start, end, maintain_selection_offset=False
                )

        # TODO: Support insert_text
        # TODO: Fallback to label
