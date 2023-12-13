from typing import Any
from typing import Optional

import pytest
from lsprotocol import types

from pytest_lsp import checks

a_range = types.Range(
    start=types.Position(line=1, character=0),
    end=types.Position(line=2, character=0),
)


@pytest.mark.parametrize(
    "capabilities,method,params,expected",
    [
        (
            types.ClientCapabilities(
                window=types.WindowClientCapabilities(work_done_progress=False)
            ),
            types.WINDOW_WORK_DONE_PROGRESS_CREATE,
            types.WorkDoneProgressCreateParams(token="id-123"),
            "does not support 'window/workDoneProgress/create'",
        ),
        (
            types.ClientCapabilities(
                window=types.WindowClientCapabilities(work_done_progress=True)
            ),
            types.WINDOW_WORK_DONE_PROGRESS_CREATE,
            types.WorkDoneProgressCreateParams(token="id-123"),
            None,
        ),
        (
            types.ClientCapabilities(
                workspace=types.WorkspaceClientCapabilities(configuration=False)
            ),
            types.WORKSPACE_CONFIGURATION,
            types.WorkspaceConfigurationParams(items=[]),
            "does not support 'workspace/configuration'",
        ),
        (
            types.ClientCapabilities(
                workspace=types.WorkspaceClientCapabilities(configuration=True)
            ),
            types.WORKSPACE_CONFIGURATION,
            types.WorkspaceConfigurationParams(items=[]),
            None,
        ),
    ],
)
def test_params_check_warning(
    capabilities: types.ClientCapabilities,
    method: str,
    params: Any,
    expected: Optional[str],
    recwarn,
):
    """Ensure that parameter checks work as expected.

    Parameters
    ----------
    capabilities
       The client's capabilities

    method
       The method name to check

    params
       The params to check

    expected
       The expected warning message

    recwarn
       Builtin fixture from pytest for recording warnings
    """

    if expected is None:
        checks.check_params_against_client_capabilities(capabilities, method, params)
        assert len(recwarn) == 0

    else:
        with pytest.warns(checks.LspSpecificationWarning, match=expected):
            checks.check_params_against_client_capabilities(
                capabilities, method, params
            )


@pytest.mark.parametrize(
    "capabilities,method,result,expected",
    [
        (
            types.ClientCapabilities(
                text_document=types.TextDocumentClientCapabilities(
                    completion=types.CompletionClientCapabilities()
                )
            ),
            types.TEXT_DOCUMENT_COMPLETION,
            [types.CompletionItem(label="item", commit_characters=["."])],
            "does not support commit characters",
        ),
        (
            types.ClientCapabilities(
                text_document=types.TextDocumentClientCapabilities(
                    completion=types.CompletionClientCapabilities(
                        completion_item=types.CompletionClientCapabilitiesCompletionItemType(
                            commit_characters_support=True
                        )
                    )
                )
            ),
            types.TEXT_DOCUMENT_COMPLETION,
            [types.CompletionItem(label="item", commit_characters=["."])],
            None,
        ),
        (
            types.ClientCapabilities(
                text_document=types.TextDocumentClientCapabilities(
                    completion=types.CompletionClientCapabilities()
                )
            ),
            types.TEXT_DOCUMENT_COMPLETION,
            [
                types.CompletionItem(
                    label="item",
                    documentation=types.MarkupContent(
                        value="", kind=types.MarkupKind.Markdown
                    ),
                )
            ],
            "does not support documentation format 'markdown'",
        ),
        (
            types.ClientCapabilities(
                text_document=types.TextDocumentClientCapabilities(
                    completion=types.CompletionClientCapabilities(
                        completion_item=types.CompletionClientCapabilitiesCompletionItemType(
                            documentation_format=[types.MarkupKind.Markdown]
                        )
                    )
                )
            ),
            types.TEXT_DOCUMENT_COMPLETION,
            [
                types.CompletionItem(
                    label="item",
                    documentation=types.MarkupContent(
                        value="", kind=types.MarkupKind.Markdown
                    ),
                )
            ],
            None,
        ),
        (
            types.ClientCapabilities(
                text_document=types.TextDocumentClientCapabilities(
                    completion=types.CompletionClientCapabilities()
                )
            ),
            types.TEXT_DOCUMENT_COMPLETION,
            [
                types.CompletionItem(
                    label="item",
                    insert_text_format=types.InsertTextFormat.Snippet,
                )
            ],
            "does not support snippets",
        ),
        (
            types.ClientCapabilities(
                text_document=types.TextDocumentClientCapabilities(
                    completion=types.CompletionClientCapabilities(
                        completion_item=types.CompletionClientCapabilitiesCompletionItemType(
                            snippet_support=True
                        )
                    )
                )
            ),
            types.TEXT_DOCUMENT_COMPLETION,
            [
                types.CompletionItem(
                    label="item",
                    insert_text_format=types.InsertTextFormat.Snippet,
                )
            ],
            None,
        ),
        (
            types.ClientCapabilities(
                text_document=types.TextDocumentClientCapabilities(
                    document_link=types.DocumentLinkClientCapabilities()
                )
            ),
            types.TEXT_DOCUMENT_DOCUMENT_LINK,
            [types.DocumentLink(range=a_range, tooltip="a tooltip")],
            "does not support tooltips",
        ),
        (
            types.ClientCapabilities(
                text_document=types.TextDocumentClientCapabilities(
                    document_link=types.DocumentLinkClientCapabilities(
                        tooltip_support=True
                    )
                )
            ),
            types.TEXT_DOCUMENT_DOCUMENT_LINK,
            [types.DocumentLink(range=a_range, tooltip="a tooltip")],
            None,
        ),
    ],
)
def test_result_check_warning(
    capabilities: types.ClientCapabilities,
    method: str,
    result: Any,
    expected: Optional[str],
    recwarn,
):
    """Ensure that parameter checks work as expected.

    Parameters
    ----------
    capabilities
       The client's capabilities

    method
       The method name to check

    params
       The params to check

    expected
       The expected warning message

    recwarn
       Builtin fixture from pytest for recording warnings
    """

    if expected is None:
        checks.check_result_against_client_capabilities(capabilities, method, result)
        assert len(recwarn) == 0

    else:
        with pytest.warns(checks.LspSpecificationWarning, match=expected):
            checks.check_result_against_client_capabilities(
                capabilities, method, result
            )

        checks.check_result_against_client_capabilities(capabilities, method, result)
