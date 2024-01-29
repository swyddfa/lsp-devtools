"""A very simple language server."""

from lsprotocol import types
from pygls.server import LanguageServer

server = LanguageServer("simple-server", "v1")


@server.feature(types.INITIALIZED)
def _(ls: LanguageServer, params: types.InitializedParams):
    ls.show_message("Hello, world!")


if __name__ == "__main__":
    server.start_io()
