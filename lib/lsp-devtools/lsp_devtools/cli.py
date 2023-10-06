import argparse
import importlib
import logging
import sys
import traceback

from lsp_devtools import __version__

logger = logging.getLogger(__name__)


BUILTIN_COMMANDS = [
    "lsp_devtools.agent",
    "lsp_devtools.client",
    "lsp_devtools.inspector",
    "lsp_devtools.record",
]


def load_command(commands: argparse._SubParsersAction, name: str):
    try:
        mod = importlib.import_module(name)
    except Exception:
        logger.warning("Unable to load command '%s'\n%s", name, traceback.format_exc())
        return

    if not hasattr(mod, "cli"):
        logger.warning("Unable to load command '%s': missing 'cli' definition", name)
        return

    try:
        mod.cli(commands)
    except Exception:
        logger.warning("Unable to load command '%s'\n%s", name, traceback.format_exc())
        return


def main():
    cli = argparse.ArgumentParser(
        prog="lsp-devtools", description="Developer tooling for language servers"
    )
    cli.add_argument("--version", action="version", version=f"%(prog)s v{__version__}")
    commands = cli.add_subparsers(title="commands")

    for mod in BUILTIN_COMMANDS:
        load_command(commands, mod)

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
