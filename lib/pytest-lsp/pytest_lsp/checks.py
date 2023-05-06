"""Checks to ensure that the server is compliant with the spec.

These can be used in your unit tests to ensure that objects (such as ``CompletionItem``
etc) take into account the client's capabilities when constructed.

However, they are also called automatically during end-to-end tests that make use of the
standard :class:`~pytest_lsp.LanguageClient`. See :ref:`pytest-lsp-spec-checks` for more
details.

"""
import logging
import warnings
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Union

from lsprotocol.types import COMPLETION_ITEM_RESOLVE
from lsprotocol.types import TEXT_DOCUMENT_COMPLETION
from lsprotocol.types import TEXT_DOCUMENT_DOCUMENT_LINK
from lsprotocol.types import ClientCapabilities
from lsprotocol.types import CompletionItem
from lsprotocol.types import CompletionList
from lsprotocol.types import DocumentLink
from lsprotocol.types import InsertTextFormat
from lsprotocol.types import MarkupContent
from pygls.capabilities import get_capability

logger = logging.getLogger(__name__)
ResultChecker = Callable[[ClientCapabilities, Any], None]
RESULT_CHECKS: Dict[str, ResultChecker] = {}


class LspSpecificationWarning(UserWarning):
    """Warning raised when encountering results that fall outside the spec."""


def check_result_for(maybe_fn: Optional[ResultChecker] = None, *, method: str):
    """Define a result check."""

    def defcheck(fn: ResultChecker):
        RESULT_CHECKS[method] = fn
        return fn

    if maybe_fn:
        return defcheck(maybe_fn)

    return defcheck


def check_result_against_client_capabilities(
    capabilities: Optional[ClientCapabilities], method: str, result: Any
):
    """Check that the given result respects the client's declared capabilities."""

    if capabilities is None:
        raise RuntimeError("Client has not been initialized")

    # Only run checks if the user provided some capabilities for the client.
    if capabilities == ClientCapabilities():
        return

    result_checker = RESULT_CHECKS.get(method, None)
    if result_checker is None:
        return

    try:
        result_checker(capabilities, result)
    except AssertionError as e:
        warnings.warn(str(e), LspSpecificationWarning, stacklevel=4)


def check_completion_item(
    item: CompletionItem,
    commit_characters_support: bool,
    documentation_formats: Set[str],
    snippet_support: bool,
):
    """Ensure that the given ``CompletionItem`` complies with the given capabilities."""

    if item.commit_characters:
        assert commit_characters_support, "Client does not support commit characters"

    if isinstance(item.documentation, MarkupContent):
        kind = item.documentation.kind
        message = f"Client does not support documentation format '{kind}'"
        assert kind in documentation_formats, message

    if item.insert_text_format == InsertTextFormat.Snippet:
        assert snippet_support, "Client does not support snippets."


@check_result_for(method=TEXT_DOCUMENT_COMPLETION)
def completion_items(
    capabilities: ClientCapabilities,
    result: Union[CompletionList, List[CompletionItem], None],
):
    """Ensure that the completion items returned from the server are compliant with the
    spec and the client's declared capabilities."""

    if result is None:
        return

    commit_characters_support = get_capability(
        capabilities,
        "text_document.completion.completion_item.commit_characters_support",
        False,
    )
    documentation_formats = set(
        get_capability(
            capabilities,
            "text_document.completion.completion_item.documentation_format",
            [],
        )
    )
    snippet_support = get_capability(
        capabilities,
        "text_document.completion.completion_item.snippet_support",
        False,
    )

    if isinstance(result, CompletionList):
        items = result.items
    else:
        items = result

    for item in items:
        check_completion_item(
            item,
            commit_characters_support=commit_characters_support,
            documentation_formats=documentation_formats,
            snippet_support=snippet_support,
        )


@check_result_for(method=COMPLETION_ITEM_RESOLVE)
def completion_item_resolve(capabilities: ClientCapabilities, item: CompletionItem):
    """Ensure that the completion item returned from the server is compliant with the
    spec and the client's declared capbabilities."""

    commit_characters_support = get_capability(
        capabilities,
        "text_document.completion.completion_item.commit_characters_support",
        False,
    )
    documentation_formats = set(
        get_capability(
            capabilities,
            "text_document.completion.completion_item.documentation_format",
            [],
        )
    )
    snippet_support = get_capability(
        capabilities,
        "text_document.completion.completion_item.snippet_support",
        False,
    )

    check_completion_item(
        item,
        commit_characters_support=commit_characters_support,
        documentation_formats=documentation_formats,
        snippet_support=snippet_support,
    )


@check_result_for(method=TEXT_DOCUMENT_DOCUMENT_LINK)
def document_links(
    capabilities: ClientCapabilities, result: Optional[List[DocumentLink]]
):
    """Ensure that the document links returned from the server are compliant with the
    Spec and the client's declared capabilities."""

    if result is None:
        return

    tooltip_support = get_capability(
        capabilities, "text_document.document_link.tooltip_support", False
    )

    for item in result:
        if item.tooltip:
            assert tooltip_support, "Client does not support tooltips."
