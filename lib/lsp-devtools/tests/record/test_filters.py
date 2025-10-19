from __future__ import annotations

import itertools
import typing

import pytest

from lsp_devtools.agent import MessageSource
from lsp_devtools.handlers.jsonrpc import JsonRPCMessage
from lsp_devtools.record.filters import JsonRPCFilter

if typing.TYPE_CHECKING:
    from typing import Any

    from lsp_devtools.record.filters import MessageSourceString


@pytest.mark.parametrize(
    "filter_source,message_source,expected",
    [
        ("both", MessageSource.CLIENT, True),
        ("both", MessageSource.SERVER, True),
        ("both", MessageSource.AGENT, False),
        ("client", MessageSource.CLIENT, True),
        ("client", MessageSource.SERVER, False),
        ("client", MessageSource.AGENT, False),
        ("server", MessageSource.CLIENT, False),
        ("server", MessageSource.SERVER, True),
        ("server", MessageSource.AGENT, False),
    ],
)
def test_filter_message_source(
    filter_source: MessageSourceString, message_source: MessageSource, expected: bool
):
    """Ensure that we can filter messages by their source correctly."""

    rpc_filter = JsonRPCFilter(message_source=filter_source)
    message = JsonRPCMessage(
        headers={"Content-Type": "application/json"},
        body={"id": "1", "method": "initialize", "params": {}},
        metadata={"source": message_source},
    )

    if expected:
        assert rpc_filter.match(message) == message
    else:
        assert rpc_filter.match(message) is None


@pytest.mark.parametrize(
    "body,setup",
    [
        # Request messages
        *itertools.product(
            [dict(id="1", method="example", params={})],
            [
                ([], True),  # empty filter = allow all
                (["request"], True),
                (["error"], False),
                (["result"], False),
                (["response"], False),
                (["notification"], False),
                (["response", "request"], True),
            ],
        ),
        # Notification messages
        *itertools.product(
            [dict(method="example", params={})],
            [
                ([], True),  # empty filter = allow all
                (["request"], False),
                (["error"], False),
                (["result"], False),
                (["response"], False),
                (["notification"], True),
                (["response", "request"], False),
                (["error", "notification"], True),
            ],
        ),
        # Result messages
        *itertools.product(
            [dict(id="1", result={})],
            [
                ([], True),  # empty filter = allow all
                (["request"], False),
                (["error"], False),
                (["result"], True),
                (["response"], True),
                (["notification"], False),
                (["response", "request"], True),
                (["error", "notification"], False),
            ],
        ),
        # Error messages
        *itertools.product(
            [dict(id="1", error={})],
            [
                ([], True),  # empty filter = allow all
                (["request"], False),
                (["error"], True),
                (["result"], False),
                (["response"], True),
                (["notification"], False),
                (["response", "request"], True),
                (["error", "notification"], True),
            ],
        ),
    ],
)
def test_filter_included_message_types(
    body: dict[str, Any], setup: tuple[list[str], bool]
):
    """Ensure that we can filter messages by listing the types we DO want to see."""

    message_types, expected = setup
    message = JsonRPCMessage(
        headers={},
        body=body,
        metadata={"source": MessageSource.CLIENT},
    )

    rpc_filter = JsonRPCFilter(include_message_types=message_types)
    rpc_filter._response_method_map["1"] = ""

    if expected:
        assert rpc_filter.match(message) == message

    else:
        assert rpc_filter.match(message) is None


@pytest.mark.parametrize(
    "body,setup",
    [
        # Request messages
        *itertools.product(
            [dict(id="1", method="example", params={})],
            [
                ([], True),  # empty filter = exclude none
                (["request"], False),
                (["error"], True),
                (["result"], True),
                (["response"], True),
                (["notification"], True),
                (["response", "request"], False),
            ],
        ),
        # Notification messages
        *itertools.product(
            [dict(method="example", params={})],
            [
                ([], True),  # empty filter = exclude none
                (["request"], True),
                (["error"], True),
                (["result"], True),
                (["response"], True),
                (["notification"], False),
                (["response", "request"], True),
                (["error", "notification"], False),
            ],
        ),
        # Result messages
        *itertools.product(
            [dict(id="1", result={})],
            [
                ([], True),  # empty filter = exclude none
                (["request"], True),
                (["error"], True),
                (["result"], False),
                (["response"], False),
                (["notification"], True),
                (["response", "request"], False),
                (["error", "notification"], True),
            ],
        ),
        # Error messages
        *itertools.product(
            [dict(id="1", error={})],
            [
                ([], True),  # empty filter = exclude none
                (["request"], True),
                (["error"], False),
                (["result"], True),
                (["response"], False),
                (["notification"], True),
                (["response", "request"], False),
                (["error", "notification"], False),
            ],
        ),
    ],
)
def test_filter_excluded_message_types(
    body: dict[str, Any], setup: tuple[list[str], bool]
):
    """Ensure that we can filter messages by listing the types we DO NOT want to see."""

    message_types, expected = setup
    message = JsonRPCMessage(
        headers={}, body=body, metadata={"source": MessageSource.CLIENT}
    )

    rpc_filter = JsonRPCFilter(exclude_message_types=message_types)
    rpc_filter._response_method_map["1"] = ""

    if expected:
        assert rpc_filter.match(message) == message
    else:
        assert rpc_filter.match(message) is None


@pytest.mark.parametrize(
    "body,setup",
    [
        # Request messages
        *itertools.product(
            [dict(id="1", method="textDocument/completion", params={})],
            [
                ([], True),  # empty filter = allow all
                (["textDocument/completion"], True),
                (["textDocument/definition"], False),
                (["textDocument/completion", "textDocument/definition"], True),
            ],
        ),
        # Notification messages
        *itertools.product(
            [dict(method="textDocument/didSave", params={})],
            [
                ([], True),  # empty filter = allow all
                (["textDocument/didSave"], True),
                (["textDocument/didClose"], False),
                (["textDocument/didSave", "textDocument/didClose"], True),
            ],
        ),
    ],
)
def test_filter_included_method(body: dict[str, Any], setup: tuple[list[str], bool]):
    """Ensure that we can filter messages by listing the methods we wish to see."""

    methods, expected = setup
    message = JsonRPCMessage(
        headers={}, body=body, metadata={"source": MessageSource.CLIENT}
    )

    rpc_filter = JsonRPCFilter(include_methods=methods)
    if expected:
        assert rpc_filter.match(message) == message
    else:
        assert rpc_filter.match(message) is None


@pytest.mark.parametrize(
    "response,setup",
    [
        # Result message
        *itertools.product(
            [dict(id="1", result={})],
            [
                ([], "textDocument/completion", True),  # empty filter = allow all
                (["textDocument/completion"], "textDocument/completion", True),
                (["textDocument/definition"], "textDocument/completion", False),
                (
                    ["textDocument/completion", "textDocument/definition"],
                    "textDocument/completion",
                    True,
                ),
            ],
        ),
        # Error message
        *itertools.product(
            [dict(id="1", error={})],
            [
                ([], "textDocument/completion", True),  # empty filter = allow all
                (["textDocument/completion"], "textDocument/completion", True),
                (["textDocument/definition"], "textDocument/completion", False),
                (
                    ["textDocument/completion", "textDocument/definition"],
                    "textDocument/completion",
                    True,
                ),
            ],
        ),
    ],
)
def test_filter_included_method_response_message(
    response: dict[str, Any], setup: tuple[list[str], str, bool]
):
    """Ensure that we can filter response message by listing the methods we wish
    to see."""

    methods, method, expected = setup
    rpc_filter = JsonRPCFilter(include_methods=methods)

    request = JsonRPCMessage(
        headers={},
        body={"id": "1", "method": method, "params": {}},
        metadata={"source": MessageSource.CLIENT},
    )

    # Needed to set the method map internally
    rpc_filter.match(request)

    message = JsonRPCMessage(
        headers={},
        body=response,
        metadata={"source": MessageSource.SERVER},
    )

    if expected:
        assert rpc_filter.match(message) == message
    else:
        assert rpc_filter.match(message) is None


@pytest.mark.parametrize(
    "body,setup",
    [
        # Request messages
        *itertools.product(
            [dict(id="1", method="textDocument/completion", params={})],
            [
                ([], True),  # empty filter = omit none
                (["textDocument/completion"], False),
                (["textDocument/definition"], True),
                (["textDocument/completion", "textDocument/definition"], False),
            ],
        ),
        # Notification messages
        *itertools.product(
            [dict(method="textDocument/didSave", params={})],
            [
                ([], True),  # empty filter = omit none
                (["textDocument/didSave"], False),
                (["textDocument/didClose"], True),
                (["textDocument/didSave", "textDocument/didClose"], False),
            ],
        ),
    ],
)
def test_filter_excluded_method(body: dict[str, Any], setup: tuple[list[str], bool]):
    """Ensure that we can filter messages by listing the methods we don't wish to
    see."""

    methods, expected = setup
    message = JsonRPCMessage(
        headers={}, body=body, metadata={"source": MessageSource.CLIENT}
    )

    rpc_filter = JsonRPCFilter(exclude_methods=methods)
    if expected:
        assert rpc_filter.match(message) == message
    else:
        assert rpc_filter.match(message) is None


@pytest.mark.parametrize(
    "response,setup",
    [
        # Result message
        *itertools.product(
            [dict(id="1", result={})],
            [
                ([], "textDocument/completion", True),  # empty filter = omit none
                (["textDocument/completion"], "textDocument/completion", False),
                (["textDocument/definition"], "textDocument/completion", True),
                (
                    ["textDocument/completion", "textDocument/definition"],
                    "textDocument/completion",
                    False,
                ),
            ],
        ),
        # Error message
        *itertools.product(
            [dict(id="1", error={})],
            [
                ([], "textDocument/completion", True),  # empty filter = omit none
                (["textDocument/completion"], "textDocument/completion", False),
                (["textDocument/definition"], "textDocument/completion", True),
                (
                    ["textDocument/completion", "textDocument/definition"],
                    "textDocument/completion",
                    False,
                ),
            ],
        ),
    ],
)
def test_filter_excluded_method_response_message(
    response: dict[str, Any], setup: tuple[list[str], str, bool]
):
    """Ensure that we can filter response message by listing the methods we dont' wish
    to see."""

    methods, method, expected = setup
    rpc_filter = JsonRPCFilter(exclude_methods=methods)

    request = JsonRPCMessage(
        headers={},
        body={"id": "1", "method": method, "params": {}},
        metadata={"source": MessageSource.CLIENT},
    )

    # Needed to set the method map internally
    rpc_filter.match(request)

    message = JsonRPCMessage(
        headers={}, body=response, metadata={"source": MessageSource.SERVER}
    )

    if expected:
        assert rpc_filter.match(message) == message
    else:
        assert rpc_filter.match(message) is None
