"""Checks to ensure that the server is compliant with the spec."""
import logging
from typing import List

from pygls.lsp.types import *

from pytest_lsp.client import Client

logger = logging.getLogger(__name__)


def warn(item: str, reason: str):
    logger.warning("Unable to check %s compliance, %s.", item, reason)


def completion_items(client: Client, items: List[CompletionItem]):
    """Ensure that the completion items returned from the server are compliant with the
    spec and the client's declared capabilities."""

    text_document = client.capabilities.text_document
    if not text_document:
        warn("CompletionItem", "missing text document capabilities")
        return

    completion = text_document.completion
    if not completion:
        warn("CompletionItem", "missing completion client capabilities")
        return

    completion_item = completion.completion_item
    if not completion_item:
        warn("CompletionItem", "missing completion item capabilities")
        return

    snippet_support = completion_item.snippet_support

    for item in items:
        if item.insert_text_format == InsertTextFormat.Snippet:
            assert snippet_support, "Client does not support snippets."
