from __future__ import annotations

import asyncio
import io
import json
import pathlib
import subprocess
import sys

import pytest

from lsp_devtools.agent import Agent

SERVER_DIR = pathlib.Path(__file__).parent / "servers"


def format_message(obj):
    content = json.dumps(obj)
    message = "".join(
        [
            f"Content-Length: {len(content)}\r\n",
            "\r\n",
            f"{content}",
        ]
    )
    return message.encode()


def echo_handler(d: bytes):
    sys.stdout.buffer.write(d)
    sys.stdout.flush()


@pytest.mark.asyncio
async def test_agent_exits():
    """Ensure that when the client closes down the lsp session and the server process
    exits, the agent does also."""

    server = await asyncio.create_subprocess_exec(
        sys.executable,
        str(SERVER_DIR / "simple.py"),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    messages = [
        format_message(
            dict(jsonrpc="2.0", id=1, method="initialize", params=dict(capabilities={}))
        ),
        format_message(dict(jsonrpc="2.0", id=2, method="shutdown", params=None)),
        format_message(dict(jsonrpc="2.0", method="exit", params=None)),
    ]

    agent = Agent(
        server,
        io.BytesIO(b"".join(messages)),
        io.BytesIO(),
        echo_handler,
    )

    try:
        await asyncio.wait_for(
            # asyncio.gather(server.wait(), agent.start()),
            agent.start(),
            timeout=10,  # s
        )
    except asyncio.CancelledError:
        pass  # The agent's tasks should be cancelled

    except TimeoutError as exc:
        # Make sure this timed out for the right reason.
        if server.returncode is None:
            raise RuntimeError("Server process did not exit") from exc

        exc.add_note("lsp-devtools agent did not stop")
