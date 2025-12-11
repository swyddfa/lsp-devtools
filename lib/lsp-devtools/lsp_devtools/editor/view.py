from __future__ import annotations

import typing

from lsprotocol import types
from textual.containers import Container
from textual.widgets import TextArea

if typing.TYPE_CHECKING:
    import pathlib

    from pygls.lsp.client import LanguageClient
    from textual.app import ComposeResult
    from textual.widgets.text_area import Edit
    from textual.widgets.text_area import EditResult


class TextEditorView(Container):
    """A view containing the text editor"""

    def compose(self) -> ComposeResult:
        text_area = LspTextArea()
        text_area.show_line_numbers = True
        yield text_area

    def open_text_document(self, path: pathlib.Path):
        """Open the given text document."""

        editor = self.query_one(LspTextArea)
        editor.open_text_document(path)


class LspTextArea(TextArea):
    """A lsp-enabled text area"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.path: pathlib.Path | None = None
        self.version = -1

    @property
    def client(self) -> LanguageClient | None:
        return self.app.client

    def open_text_document(self, path: pathlib.Path):
        """Open the given text document."""

        text = path.read_text()

        # Currently we only support one open file at a time, so be sure to
        # close the currently active file, if necessary.
        if self.path and self.client is not None:
            self.client.text_document_did_close(
                types.DidCloseTextDocumentParams(
                    types.TextDocumentIdentifier(self.path.as_uri())
                )
            )

        self.load_text(text)
        self.path = path

        if self.client is not None:
            self.client.text_document_did_open(
                types.DidOpenTextDocumentParams(
                    types.TextDocumentItem(
                        path.as_uri(),
                        language_id="plaintext",
                        version=1,
                        text=text,
                    )
                )
            )

    def edit(self, edit: Edit) -> EditResult:
        """Extend the base ``edit()`` method to.

        - Ensure that any edits that are made to the document are syncronised with the
          server.
        """
        result = super().edit(edit)

        if self.path is None or self.client is None:
            return result

        self.version += 1
        start_line, start_col = edit.from_location
        end_line, end_col = edit.to_location

        self.client.text_document_did_change(
            types.DidChangeTextDocumentParams(
                text_document=types.VersionedTextDocumentIdentifier(
                    version=self.version, uri=self.path.as_uri()
                ),
                content_changes=[
                    types.TextDocumentContentChangePartial(
                        text=edit.text,
                        range=types.Range(
                            start=types.Position(line=start_line, character=start_col),
                            end=types.Position(line=end_line, character=end_col),
                        ),
                    )
                ],
            )
        )

        return result
