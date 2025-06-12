from __future__ import annotations

import asyncio
import sys
import typing

import pytest
import stamina

from lsp_devtools.agent import MessageSource
from lsp_devtools.handlers.jsonrpc import JsonRPCMessage

if typing.TYPE_CHECKING:
    import pathlib
    from typing import Any


@pytest.mark.parametrize(
    "args, messages, expected",
    [
        (
            None,
            [
                JsonRPCMessage.client(
                    {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
                )
            ],
            '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}\n',
        ),
        (
            ["-f", "{message:jsonl}"],
            [
                JsonRPCMessage.client(
                    {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
                )
            ],
            '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}\n',
        ),
        (
            ["-f", "{message:json}"],
            [
                JsonRPCMessage.client(
                    {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
                )
            ],
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
            ["-f", "{message.method}"],
            [
                JsonRPCMessage.client(
                    {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
                ),
                JsonRPCMessage.server({"jsonrpc": "2.0", "id": 1, "result": {}}),
            ],
            "initialize\n",
        ),
        (
            ["-f", "{message.id}"],
            [
                JsonRPCMessage.client(
                    {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
                ),
                JsonRPCMessage.server({"jsonrpc": "2.0", "id": 1, "result": {}}),
            ],
            "1\n1\n",
        ),
    ],
)
@pytest.mark.asyncio
async def test_file_output(
    tmp_path: pathlib.Path,
    args: list[str] | None,
    messages: list[JsonRPCMessage],
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

    host = "localhost"
    port = 8765

    log = tmp_path / "log.json"
    # fmt: off
    cli_args = [
        "-m", "lsp_devtools", "record",
        "--bind", str(host),
        "--port", str(port),
        "--on-disconnect", "exit",
        "--to-file", str(log),
        *(args or []),
    ]
    # fmt: on
    print(f"Running command: python {' '.join(cli_args)}")
    process = await asyncio.create_subprocess_exec(sys.executable, *cli_args)

    async for attempt in stamina.retry_context(on=OSError, attempts=5, timeout=5):
        with attempt:
            print("Trying to connect")
            reader, writer = await asyncio.open_connection(host, port)

    print("Connected. Sending messages...")
    for message in messages:
        writer.write(message.to_wire_format())
        await writer.drain()

    print("Closing connection")
    writer.close()
    await asyncio.wait_for(process.wait(), timeout=5.0)

    print(log.read_text())
    assert log.read_text() == expected
