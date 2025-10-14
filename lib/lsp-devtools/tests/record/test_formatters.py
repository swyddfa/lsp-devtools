from __future__ import annotations

import json

import pytest

from lsp_devtools.record.formatters import ValueFormatter


@pytest.mark.parametrize(
    "fmt,message,expected",
    [
        ("I am a literal string", {}, "I am a literal string"),
        (
            "{message.method}",
            {"method": "textDocument/completion"},
            "textDocument/completion",
        ),
        (
            "The method is: {message.method}",
            {"method": "textDocument/completion"},
            "The method is: textDocument/completion",
        ),
        (
            "The method {message.method!r} was called",
            {"method": "textDocument/completion"},
            "The method 'textDocument/completion' was called",
        ),
        (
            "{message.position:json}",
            {
                "position": {"line": 1, "character": 2},
            },
            '{\n  "line": 1,\n  "character": 2\n}',
        ),
        (
            "{message.position:json-compact}",
            {
                "position": {"line": 1, "character": 2},
            },
            '{"line": 1, "character": 2}',
        ),
        (
            "{message.method} {message.params.textDocument.uri}:{message.params.position}",
            {
                "method": "textDocument/completion",
                "params": {
                    "position": {"line": 1, "character": 2},
                    "textDocument": {"uri": "file:///path/to/file.txt"},
                },
            },
            'textDocument/completion file:///path/to/file.txt:{\n  "line": 1,\n  "character": 2\n}',
        ),
        (
            "{message.method} {message.params.textDocument.uri}:{message.params.position:Position}",
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
            "{message.params.range:Range}",
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
        ("{message.params.type:MessageType}", {"params": {"type": 4}}, "Log"),
        (
            "{message.params.type:CompletionItemKind}",
            {"params": {"type": 4}},
            "Constructor",
        ),
        (
            "{message.result.items}",
            {
                "result": {
                    "items": [{"label": "one"}, {"label": "two"}, {"label": "three"}]
                }
            },
            json.dumps(
                [{"label": "one"}, {"label": "two"}, {"label": "three"}], indent=2
            ),
        ),
        (
            "{message.result.items[:].label}",
            {
                "result": {
                    "items": [{"label": "one"}, {"label": "two"}, {"label": "three"}]
                }
            },
            '[\n  "one",\n  "two",\n  "three"\n]',
        ),
        (
            "{message.result.items.label}",
            {
                "result": {
                    "items": [{"label": "one"}, {"label": "two"}, {"label": "three"}]
                }
            },
            '[\n  "one",\n  "two",\n  "three"\n]',
        ),
        (
            "{message.result.items[0]}",
            {
                "result": {
                    "items": [{"label": "one"}, {"label": "two"}, {"label": "three"}]
                }
            },
            '{\n  "label": "one"\n}',
        ),
        (
            "{message.result.items[-1]}",
            {
                "result": {
                    "items": [{"label": "one"}, {"label": "two"}, {"label": "three"}]
                }
            },
            '{\n  "label": "three"\n}',
        ),
        (
            "- {message.result.items[0].label}",
            {
                "result": {
                    "items": [{"label": "one"}, {"label": "two"}, {"label": "three"}]
                }
            },
            "- one",
        ),
        (
            "{message.result.items[0:2].label}",
            {
                "result": {
                    "items": [{"label": "one"}, {"label": "two"}, {"label": "three"}]
                }
            },
            '[\n  "one",\n  "two"\n]',
        ),
        (
            '{{"clientInfo": {message.params.clientInfo}, '
            '"capabilities": {message.params.capabilities}}}',
            {
                "params": {
                    "clientInfo": {"name": "Client", "version": "1.0"},
                    "capabilities": {"workspace": {"symbol": True}},
                }
            },
            '{"clientInfo": {\n'
            '  "name": "Client",\n'
            '  "version": "1.0"\n'
            '}, "capabilities": {\n'
            '  "workspace": {\n'
            '    "symbol": true\n'
            "  }\n"
            "}}",
        ),
    ],
)
def test_format_string(fmt: str, message: dict[str, Any], expected: str):
    """Ensure that we can format strings correctly."""
    assert expected == fmt.format(message=ValueFormatter(message))
