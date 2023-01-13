"""Checks to ensure that the server is compliant with the spec."""
import logging
from typing import List

from lsprotocol.types import CompletionItem
from lsprotocol.types import DocumentLink
from lsprotocol.types import InsertTextFormat
from lsprotocol.types import MarkupContent
from pygls.capabilities import get_capability
from pytest_lsp.client import LanguageClient

logger = logging.getLogger(__name__)


def completion_items(client: LanguageClient, items: List[CompletionItem]):
    """Ensure that the completion items returned from the server are compliant with the
    spec and the client's declared capabilities."""

    commit_characters_support = get_capability(
        client.capabilities,
        "text_document.completion.completion_item.commit_characters_support",
        False,
    )
    documentation_formats = set(
        get_capability(
            client.capabilities,
            "text_document.completion.completion_item.documentation_format",
            [],
        )
    )
    snippet_support = get_capability(
        client.capabilities,
        "text_document.completion.completion_item.snippet_support",
        False,
    )

    for item in items:

        if item.commit_characters:
            assert (
                commit_characters_support
            ), "Client does not support commit characters"

        if isinstance(item.documentation, MarkupContent):
            kind = item.documentation.kind
            assert (
                kind in documentation_formats
            ), f"Client does not support documentation format '{kind}'"

        if item.insert_text_format == InsertTextFormat.Snippet:
            assert snippet_support, "Client does not support snippets."


def document_links(client: LanguageClient, items: List[DocumentLink]):
    """Ensure that the document links returned from the server are compliant with the
    spec and the client's declared capabilities."""

    tooltip_support = get_capability(
        client.capabilities, "text_document.document_link.tooltip_support", False
    )

    for item in items:
        if item.tooltip:
            assert tooltip_support, "Client does not support tooltips."
