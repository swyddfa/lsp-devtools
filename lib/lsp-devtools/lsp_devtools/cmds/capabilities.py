import argparse
import json

from pygls.lsp.methods import INITIALIZE
from pygls.lsp.types import InitializeParams
from pygls.server import LanguageServer


def capabilities(args, extra):

    server = LanguageServer()

    @server.feature(INITIALIZE)
    def on_initialize(ls, params: InitializeParams):
        client_info = params.client_info
        if client_info:
            client_name = client_info.name.lower().replace(" ", "_")
            client_version = client_info.version or "unknown"
        else:
            client_name = "unknown"
            client_version = "unknown"

        filename = f"{client_name}_v{client_version}.json"
        with open(filename, "w") as f:
            json.dump(params.capabilities.dict(), f, indent=2)

    server.start_io()


def cli(commands: argparse._SubParsersAction):
    cmd = commands.add_parser(
        "capabilities",
        help="dummy lsp server for recording a client's capabilities.",
    )
    cmd.set_defaults(run=capabilities)
