from typing import Any

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
                workspace=types.WorkspaceClientCapabilities(configuration=False)
            ),
            types.WORKSPACE_CONFIGURATION,
            types.WorkspaceConfigurationParams(items=[]),
            "does not support 'workspace/configuration'",
        ),
    ],
)
def test_params_check_warning(
    capabilities: types.ClientCapabilities, method: str, params: Any, expected: str
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
    """

    with pytest.warns(checks.LspSpecificationWarning, match=expected):
        checks.check_params_against_client_capabilities(capabilities, method, params)


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
                    document_link=types.DocumentLinkClientCapabilities(
                        tooltip_support=False
                    )
                )
            ),
            types.TEXT_DOCUMENT_DOCUMENT_LINK,
            [types.DocumentLink(range=a_range, tooltip="a tooltip")],
            "does not support tooltips",
        ),
    ],
)
def test_result_check_warning(
    capabilities: types.ClientCapabilities, method: str, result: Any, expected: str
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
    """

    with pytest.warns(checks.LspSpecificationWarning, match=expected):
        checks.check_result_against_client_capabilities(capabilities, method, result)
