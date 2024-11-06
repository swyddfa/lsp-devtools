import itertools
import logging

import pytest

from lsp_devtools.record.filters import LSPFilter


@pytest.mark.parametrize(
    "filter_source,message_source,expected",
    [
        ("both", "client", True),
        ("both", "server", True),
        ("client", "client", True),
        ("client", "server", False),
        ("server", "client", False),
        ("server", "server", True),
    ],
)
def test_filter_message_source(filter_source: str, message_source: str, expected: bool):
    """Ensure that we can filter messages by their source correctly."""

    lsp = LSPFilter(message_source=filter_source)
    message = dict(id="1", method="initialize", params={})

    record = logging.LogRecord("example", logging.INFO, "", 0, "%s", message, None)
    record.__dict__["Message-Source"] = message_source

    assert lsp.filter(record) is expected


@pytest.mark.parametrize(
    "message,setup",
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
def test_filter_included_message_types(message: dict, setup: tuple[list[str], bool]):
    """Ensure that we can filter messages by listing the types we DO want to see."""

    message_types, expected = setup
    record = logging.LogRecord("example", logging.INFO, "", 0, "%s", message, None)
    record.__dict__["Message-Source"] = "client"

    lsp = LSPFilter(include_message_types=message_types)
    lsp._response_method_map["1"] = ""

    assert lsp.filter(record) is expected


@pytest.mark.parametrize(
    "message,setup",
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
def test_filter_excluded_message_types(message: dict, setup: tuple[list[str], bool]):
    """Ensure that we can filter messages by listing the types we DO NOT want to see."""

    message_types, expected = setup
    record = logging.LogRecord("example", logging.INFO, "", 0, "%s", message, None)
    record.__dict__["Message-Source"] = "client"

    lsp = LSPFilter(exclude_message_types=message_types)
    lsp._response_method_map["1"] = ""

    assert lsp.filter(record) is expected


@pytest.mark.parametrize(
    "message,setup",
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
def test_filter_included_method(message: dict, setup: tuple[list[str], bool]):
    """Ensure that we can filter messages by listing the methods we wish to see."""

    methods, expected = setup
    record = logging.LogRecord("example", logging.INFO, "", 0, "%s", message, None)
    record.__dict__["Message-Source"] = "client"

    lsp = LSPFilter(include_methods=methods)
    assert lsp.filter(record) is expected


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
    response: dict, setup: tuple[list[str], str, bool]
):
    """Ensure that we can filter response message by listing the methods we wish
    to see."""

    methods, method, expected = setup
    lsp = LSPFilter(include_methods=methods)

    request = dict(id="1", method=method, params={})
    record = logging.LogRecord("example", logging.INFO, "", 0, "%s", request, None)
    record.__dict__["Message-Source"] = "client"

    lsp.filter(record)

    record = logging.LogRecord("example", logging.INFO, "", 0, "%s", response, None)
    record.__dict__["Message-Source"] = "server"

    assert lsp.filter(record) is expected


@pytest.mark.parametrize(
    "message,setup",
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
def test_filter_excluded_method(message: dict, setup: tuple[list[str], bool]):
    """Ensure that we can filter messages by listing the methods we don't wish to
    see."""

    methods, expected = setup
    record = logging.LogRecord("example", logging.INFO, "", 0, "%s", message, None)
    record.__dict__["Message-Source"] = "client"

    lsp = LSPFilter(exclude_methods=methods)
    assert lsp.filter(record) is expected


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
    response: dict, setup: tuple[list[str], str, bool]
):
    """Ensure that we can filter response message by listing the methods we dont' wish
    to see."""

    methods, method, expected = setup
    lsp = LSPFilter(exclude_methods=methods)

    request = dict(id="1", method=method, params={})
    record = logging.LogRecord("example", logging.INFO, "", 0, "%s", request, None)
    record.__dict__["Message-Source"] = "client"

    lsp.filter(record)

    record = logging.LogRecord("example", logging.INFO, "", 0, "%s", response, None)
    record.__dict__["Message-Source"] = "server"

    assert lsp.filter(record) is expected


def test_filter_skip_unformattable_message():
    """Ensure that if a message cannot be formatted it is skipped."""

    lsp = LSPFilter(formatter="{.xxx}")

    request = dict(id="1", method="textDocument/completion", params={})
    record = logging.LogRecord("example", logging.INFO, "", 0, "%s", request, None)
    record.__dict__["Message-Source"] = "client"

    lsp.filter(record)
    assert lsp.filter(record) is False


def test_filter_format_message():
    """Ensure that we can format a message according to some string."""

    lsp = LSPFilter(formatter="{.params.textDocument.uri}")

    request = dict(
        id="1",
        method="textDocument/completion",
        params=dict(textDocument=dict(uri="file:///path/to/file.txt")),
    )
    record = logging.LogRecord("example", logging.INFO, "", 0, "%s", request, None)
    record.__dict__["Message-Source"] = "client"

    assert lsp.filter(record) is True
    assert record.msg == "file:///path/to/file.txt"
