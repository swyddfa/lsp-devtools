import argparse
import logging
import os
import pathlib
import subprocess
import sys

from typing import List

import appdirs

from lsp_devtools import __version__
from lsp_devtools.agent import Agent
from lsp_devtools.handlers.prometheus import PrometheusHandler
from lsp_devtools.handlers.sql import SqlHandler


def agent(args, extra: List[str]):
    """Run the LSP agent."""

    if extra is None:
        print("Missing server start command", file=sys.stderr)
        return 1

    dbpath = pathlib.Path(args.db)
    if not dbpath.parent.exists():
        dbpath.parent.mkdir(parents=True)

    cmd = [sys.executable, "-m", "esbonio"]
    server_process = subprocess.Popen(
        cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE
    )

    logger = logging.getLogger("lsp_devtools.agent")
    logger.setLevel(logging.INFO)

    sql_handler = SqlHandler(dbpath)
    sql_handler.setLevel(logging.INFO)

    prometheus_handler = PrometheusHandler()
    prometheus_handler.setLevel(logging.INFO)

    logger.addHandler(sql_handler)
    logger.addHandler(prometheus_handler)

    agent = Agent(server_process, sys.stdin.buffer, sys.stdout.buffer)
    agent.start()
    agent.join()


cli = argparse.ArgumentParser(
    prog="lsp-devtools", description="Development tooling for language servers"
)
commands = cli.add_subparsers(title="commands")

agent_cmd = commands.add_parser(
    "agent", help="agent for recording communications between an LSP client and server."
)
agent_cmd.add_argument(
    "--db",
    help="path to use for the database",
    default=os.path.join(
        appdirs.user_data_dir(appname="lsp-devtools"), "lsp_sessions.db"
    ),
)
agent_cmd.set_defaults(run=agent)


def main():
    try:
        idx = sys.argv.index("--")
        args, extra = sys.argv[1:idx], sys.argv[idx + 1 :]
    except ValueError:
        args, extra = sys.argv[1:], None

    parsed_args = cli.parse_args(args)

    if hasattr(parsed_args, "run"):
        return parsed_args.run(parsed_args, extra)

    cli.print_help()
    return 0
