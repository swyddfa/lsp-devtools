"""Record an LSP session."""
import argparse
import logging
import subprocess
import sys
from typing import List

from lsp_devtools.agent import Agent
from lsp_devtools.agent import logger


class DebugOnly(logging.Filter):
    """Only permits messages at debug level."""

    def filter(self, record: logging.LogRecord):
        return record.levelno == logging.DEBUG and "source" in record.__dict__


def record(args, extra: List[str]):

    if extra is None:
        print("Missing server start command", file=sys.stderr)
        return 1

    log_level = logging.DEBUG if args.raw else logging.INFO

    process = subprocess.Popen(extra, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    logger.setLevel(log_level)

    handler = logging.FileHandler(args.file, mode="w")
    handler.setLevel(log_level)
    handler.setFormatter(logging.Formatter(args.format))

    if args.raw:
        handler.addFilter(DebugOnly())

    logger.addHandler(handler)

    agent = Agent(process, sys.stdin.buffer, sys.stdout.buffer)
    agent.start()
    agent.join()


def cli(commands: argparse._SubParsersAction):
    cmd = commands.add_parser(
        "record",
        help="record an LSP session.",
        description="""\
This command runs the given language server command as a subprocess and records all
messages sent between client and server.
""",
    )  # type: argparse.ArgumentParser

    output = cmd.add_mutually_exclusive_group()
    output.add_argument(
        "-f",
        "--file",
        help="save the log to a text file with the given filename",
        default="lsp.log",
    )
    # output.add_argument(
    #     "--db",
    #     help="save the log to a SQLite db with the given filename",
    #     default=None,
    # )

    fileopts = cmd.add_argument_group(
        title="file options",
        description="these options only apply when --file is used",
    )
    fileopts.add_argument(
        "-r",
        "--raw",
        help="record all data, not just parsed messages",
        action="store_true",
    )
    fileopts.add_argument(
        "--format",
        help="format string to use with the log messages",
        default="%(message)s",
    )

    cmd.set_defaults(run=record)
