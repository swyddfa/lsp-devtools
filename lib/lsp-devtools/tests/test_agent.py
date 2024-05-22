import asyncio
import json
import os
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

    (stdin_read, stdin_write) = os.pipe()
    (stdout_read, stdout_write) = os.pipe()

    server = await asyncio.create_subprocess_exec(
        sys.executable,
        str(SERVER_DIR / "simple.py"),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    agent = Agent(
        server,
        os.fdopen(stdin_read, mode="rb"),
        os.fdopen(stdout_write, mode="wb"),
        echo_handler,
    )

    os.write(
        stdin_write,
        format_message(
            dict(jsonrpc="2.0", id=1, method="initialize", params=dict(capabilities={}))
        ),
    )

    os.write(
        stdin_write,
        format_message(dict(jsonrpc="2.0", id=2, method="shutdown", params=None)),
    )

    os.write(
        stdin_write,
        format_message(dict(jsonrpc="2.0", method="exit", params=None)),
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
