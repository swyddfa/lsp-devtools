"""Checks to ensure that the server is compliant with the spec.

These can be used in your unit tests to ensure that objects (such as ``CompletionItem``
etc) take into account the client's capabilities when constructed.

However, they are also called automatically during end-to-end tests that make use of the
standard :class:`~pytest_lsp.LanguageClient`. See :ref:`pytest-lsp-spec-checks` for more
details.

"""

# ruff: noqa: S101
import logging
import warnings
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Union

from lsprotocol import types
from pygls.capabilities import get_capability

logger = logging.getLogger(__name__)
ParamsChecker = Callable[[types.ClientCapabilities, Any], None]
ResultChecker = Callable[[types.ClientCapabilities, Any], None]

PARAMS_CHECKS: Dict[str, ParamsChecker] = {}
RESULT_CHECKS: Dict[str, ResultChecker] = {}


class LspSpecificationWarning(UserWarning):
    """Warning raised when encountering results that fall outside the spec."""


def check_result_for(*, method: str) -> Callable[[ResultChecker], ResultChecker]:
    """Define a result check."""

    def defcheck(fn: ResultChecker):
        if (existing := RESULT_CHECKS.get(method)) is not None:
            raise ValueError(f"{fn!r} conflicts with existing check {existing!r}")

        RESULT_CHECKS[method] = fn
        return fn

    return defcheck


def check_params_of(*, method: str) -> Callable[[ParamsChecker], ParamsChecker]:
    """Define a params check."""

    def defcheck(fn: ParamsChecker):
        if (existing := PARAMS_CHECKS.get(method)) is not None:
            raise ValueError(f"{fn!r} conflicts with existing check {existing!r}")

        PARAMS_CHECKS[method] = fn
        return fn

    return defcheck


def check_result_against_client_capabilities(
    capabilities: Optional[types.ClientCapabilities], method: str, result: Any
):
    """Check that the given result respects the client's declared capabilities.

    This will emit an ``LspSpecificationWarning`` if any issues are detected.

    Parameters
    ----------
    capabilities
       The client's capabilities

    method
       The method name to validate the result of

    result
       The result to validate
    """

    if capabilities is None:
        raise RuntimeError("Client has not been initialized")

    # Only run checks if the user provided some capabilities for the client.
    if capabilities == types.ClientCapabilities():
        return

    result_checker = RESULT_CHECKS.get(method)
    if result_checker is None:
        return

    try:
        result_checker(capabilities, result)
    except AssertionError as e:
        warnings.warn(str(e), LspSpecificationWarning, stacklevel=4)


def check_params_against_client_capabilities(
    capabilities: Optional[types.ClientCapabilities], method: str, params: Any
):
    """Check that the given params respect the client's declared capabilities.

    This will emit an ``LspSpecificationWarning`` if any issues are detected.

    Parameters
    ----------
    capabilities
       The client's capabilities

    method
       The method name to validate the result of

    params
       The params to validate
    """
    if capabilities is None:
        raise RuntimeError("Client has not been initialized")

    # Only run checks if the user provided some capabilities for the client.
    if capabilities == types.ClientCapabilities():
        return

    params_checker = PARAMS_CHECKS.get(method)
    if params_checker is None:
        return

    try:
        params_checker(capabilities, params)
    except AssertionError as e:
        warnings.warn(str(e), LspSpecificationWarning, stacklevel=2)


def check_completion_item(
    item: types.CompletionItem,
    commit_characters_support: bool,
    documentation_formats: Set[str],
    snippet_support: bool,
):
    """Ensure that the given ``CompletionItem`` complies with the given capabilities."""

    if item.commit_characters:
        assert commit_characters_support, "Client does not support commit characters"

    if isinstance(item.documentation, types.MarkupContent):
        kind = item.documentation.kind
        message = f"Client does not support documentation format {kind.value!r}"
        assert kind in documentation_formats, message

    if item.insert_text_format == types.InsertTextFormat.Snippet:
        assert snippet_support, "Client does not support snippets."


@check_result_for(method=types.TEXT_DOCUMENT_COMPLETION)
def completion_items(
    capabilities: types.ClientCapabilities,
    result: Union[types.CompletionList, List[types.CompletionItem], None],
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

    if isinstance(result, types.CompletionList):
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


@check_result_for(method=types.COMPLETION_ITEM_RESOLVE)
def completion_item_resolve(
    capabilities: types.ClientCapabilities, item: types.CompletionItem
):
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


@check_result_for(method=types.TEXT_DOCUMENT_DOCUMENT_LINK)
def document_links(
    capabilities: types.ClientCapabilities, result: Optional[List[types.DocumentLink]]
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


@check_params_of(method=types.WINDOW_WORK_DONE_PROGRESS_CREATE)
def work_done_progress_create(
    capabilities: types.ClientCapabilities,
    params: types.WorkDoneProgressCreateParams,
):
    """Assert that the client has support for ``window/workDoneProgress/create``
    requests."""
    is_supported = get_capability(capabilities, "window.work_done_progress", False)
    assert is_supported, "Client does not support 'window/workDoneProgress/create'"


@check_params_of(method=types.WORKSPACE_CONFIGURATION)
def workspace_configuration(
    capabilities: types.ClientCapabilities,
    params: types.WorkspaceConfigurationParams,
):
    """Ensure that the client has support for ``workspace/configuration`` requests."""
    is_supported = get_capability(capabilities, "workspace.configuration", False)
    assert is_supported, "Client does not support 'workspace/configuration'"
