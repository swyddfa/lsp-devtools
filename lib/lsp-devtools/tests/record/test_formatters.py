import pytest

from lsp_devtools.record.formatters import FormatString


@pytest.mark.parametrize(
    "pattern,message,expected",
    [
        ("I am a literal string", {}, "I am a literal string"),
        ("{.method}", {"method": "textDocument/completion"}, "textDocument/completion"),
        (
            "The method is: {.method}",
            {"method": "textDocument/completion"},
            "The method is: textDocument/completion",
        ),
        (
            "The method '{.method}' was called",
            {"method": "textDocument/completion"},
            "The method 'textDocument/completion' was called",
        ),
        (
            "{.method} {.params.textDocument.uri}:{.params.position}",
            {
                "method": "textDocument/completion",
                "params": {
                    "position": {"line": 1, "character": 2},
                    "textDocument": {"uri": "file:///path/to/file.txt"},
                },
            },
            "textDocument/completion file:///path/to/file.txt:{'line': 1, 'character': 2}",
        ),
        (
            "{.method} {.params.textDocument.uri}:{.params.position|Position}",
            {
                "method": "textDocument/completion",
                "params": {
                    "position": {"line": 1, "character": 2},
                    "textDocument": {"uri": "file:///path/to/file.txt"},
                },
            },
            "textDocument/completion file:///path/to/file.txt:1:2",
        ),
        (
            "{.params.range|Range}",
            {
                "params": {
                    "range": {
                        "start": {"line": 1, "character": 2},
                        "end": {"line": 3, "character": 4},
                    }
                }
            },
            "1:2-3:4",
        ),
        ("{.params.type|MessageType}", {"params": {"type": 4}}, "Log"),
        ("{.params.type|CompletionItemKind}", {"params": {"type": 4}}, "Constructor"),
        (
            "{.result.items[]}",
            {
                "result": {
                    "items": [{"label": "one"}, {"label": "two"}, {"label": "three"}]
                }
            },
            "{'label': 'one'}\n{'label': 'two'}\n{'label': 'three'}",
        ),
        (
            "{.result.items[].label}",
            {
                "result": {
                    "items": [{"label": "one"}, {"label": "two"}, {"label": "three"}]
                }
            },
            "one\ntwo\nthree",
        ),
        (
            "- {.result.items[\\n- ].label}",
            {
                "result": {
                    "items": [{"label": "one"}, {"label": "two"}, {"label": "three"}]
                }
            },
            "- one\n- two\n- three",
        ),
        (
            "{.result.items[0]}",
            {
                "result": {
                    "items": [{"label": "one"}, {"label": "two"}, {"label": "three"}]
                }
            },
            "{'label': 'one'}",
        ),
        (
            "{.result.items[-1]}",
            {
                "result": {
                    "items": [{"label": "one"}, {"label": "two"}, {"label": "three"}]
                }
            },
            "{'label': 'three'}",
        ),
        (
            "- {.result.items[0].label}",
            {
                "result": {
                    "items": [{"label": "one"}, {"label": "two"}, {"label": "three"}]
                }
            },
            "- one",
        ),
        (
            "{.result.items[0:2].label}",
            {
                "result": {
                    "items": [{"label": "one"}, {"label": "two"}, {"label": "three"}]
                }
            },
            "one\ntwo",
        ),
        (
            "- {.result.items[0:2#\\n- ].label}",
            {
                "result": {
                    "items": [{"label": "one"}, {"label": "two"}, {"label": "three"}]
                }
            },
            "- one\n- two",
        ),
    ],
)
def test_format_string(pattern: str, message: dict, expected: str):
    """Ensure that we can format strings correctly."""

    fmt = FormatString(pattern)
    assert expected == fmt.format(message)
