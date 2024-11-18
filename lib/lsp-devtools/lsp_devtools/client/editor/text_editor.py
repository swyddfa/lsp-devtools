from __future__ import annotations

import contextlib
import pathlib
import typing
from typing import Union

from lsprotocol import types
from pygls import uris as uri
from pygls.capabilities import get_capability
from textual.message import Message
from textual.widgets import TextArea

if typing.TYPE_CHECKING:
    from lsp_devtools.client.lsp import LanguageClient

CompletionResult = Union[list[types.CompletionItem], types.CompletionList, None]


# TODO: Refactor to
#       - emit relevent events.
#       - split handlers out into multiple features that can listen and respond
#         to these events..
class TextEditor(TextArea):
    """A wrapper around textual's ``TextArea`` widget."""

    class Completion(Message):
        """Emitted when completion results are received."""

        def __init__(self, result: CompletionResult):
            self.result = result
            super().__init__()

    def __init__(self, lsp_client: LanguageClient, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.uri = None
        self.version = 0

        self.lsp_client = lsp_client
        self.suppress_completion = False

    @contextlib.contextmanager
    def set_state(self, **kwargs):
        """Temporarily override a value on the editor."""
        old_values = {}
        for key, value in kwargs.items():
            old_values[key] = getattr(self, key)
            setattr(self, key, value)

        yield

        for key, value in old_values.items():
            setattr(self, key, value)

    @property
    def completion_triggers(self):
        """Return the completion trigger characters registered by the server."""
        return get_capability(
            self.lsp_client.server_capabilities,  # type: ignore
            "completion_provider.trigger_characters",
            set(),
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
        """Extend the base ``edit()`` method to.

        - Ensure that any edits that are made to the document are syncronised with the
          server.
        - Completions are triggered if necessary.
        """
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

        if len(edit.text) == 0:
            return

        char = edit.text[-1]
        if not self.suppress_completion and char in self.completion_triggers:
            # TODO: How to send $/cancelRequest if a worker is cancelled?
            self.run_worker(
                self.trigger_completion(end_line, end_col),
                group="lsp-completion",
                exclusive=True,
            )

    async def trigger_completion(self, line: int, character: int):
        """Trigger completion at the given location."""

        if self.uri is None:
            return

        result = await self.lsp_client.text_document_completion_async(
            types.CompletionParams(
                text_document=types.TextDocumentIdentifier(uri=self.uri),
                position=types.Position(line=line, character=character),
            )
        )

        self.post_message(self.Completion(result))
