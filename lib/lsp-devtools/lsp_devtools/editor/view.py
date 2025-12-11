from __future__ import annotations

import typing

from lsprotocol import types
from textual.containers import Container
from textual.widgets import TextArea

if typing.TYPE_CHECKING:
    import pathlib

    from pygls.lsp.client import LanguageClient
    from textual.app import ComposeResult


class TextEditorView(Container):
    """A view containing the text editor"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.path: pathlib.Path | None = None

    def compose(self) -> ComposeResult:
        text_area = TextArea()
        text_area.show_line_numbers = True
        yield text_area

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

        editor = self.query_one(TextArea)
        editor.text = text
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
