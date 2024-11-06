from __future__ import annotations

import argparse
import logging
import typing

import pytest

from lsp_devtools.record import cli
from lsp_devtools.record import setup_file_output

if typing.TYPE_CHECKING:
    import pathlib
    from typing import Any


@pytest.fixture(scope="module")
def record():
    """Return a cli parser for the record command."""
    parser = argparse.ArgumentParser(description="for testing purposes")
    commands = parser.add_subparsers()
    cli(commands)

    return parser


@pytest.fixture
def logger():
    """Return the logger instance to use."""

    log = logging.getLogger(__name__)
    log.setLevel(logging.INFO)

    for handler in log.handlers:
        log.removeHandler(handler)

    return log


@pytest.mark.parametrize(
    "args, messages, expected",
    [
        (
            [],
            [dict(jsonrpc="2.0", id=1, method="initialize", params=dict())],
            '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}\n',
        ),
        (
            ["-f", "{.|json-compact}"],
            [dict(jsonrpc="2.0", id=1, method="initialize", params=dict())],
            '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}\n',
        ),
        (
            ["-f", "{.|json}"],
            [dict(jsonrpc="2.0", id=1, method="initialize", params=dict())],
            "\n".join(
                [
                    "{",
                    '  "jsonrpc": "2.0",',
                    '  "id": 1,',
                    '  "method": "initialize",',
                    '  "params": {}',
                    "}",
                    "",
                ]
            ),
        ),
        (
            ["-f", "{.method|json}"],
            [
                dict(jsonrpc="2.0", id=1, method="initialize", params=dict()),
                dict(jsonrpc="2.0", id=1, result=dict()),
            ],
            "initialize\n",
        ),
        (
            ["-f", "{.id}"],
            [
                dict(jsonrpc="2.0", id=1, method="initialize", params=dict()),
                dict(jsonrpc="2.0", id=1, result=dict()),
            ],
            "1\n1\n",
        ),
    ],
)
def test_file_output(
    tmp_path: pathlib.Path,
    record: argparse.ArgumentParser,
    logger: logging.Logger,
    args: list[str],
    messages: list[dict[str, Any]],
    expected: str,
):
    """Ensure that we can log to files correctly.

    Parameters
    ----------
    tmp_path
       pytest's ``tmp_path`` fixture

    record
       The record command's cli parser

    logger
       The logging instance to use

    messages
       The messages to record

    expected
       The expected file output.
    """
    log = tmp_path / "log.json"
    parsed_args = record.parse_args(["record", "--to-file", str(log), *args])

    setup_file_output(parsed_args, logger)

    for message in messages:
        logger.info("%s", message, extra={"Message-Source": "client"})

    assert log.read_text() == expected
