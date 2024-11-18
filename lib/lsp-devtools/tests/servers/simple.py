"""A very simple language server."""

from lsprotocol import types
from pygls.lsp.server import LanguageServer

server = LanguageServer("simple-server", "v1")


@server.feature(types.INITIALIZED)
def _(ls: LanguageServer, params: types.InitializedParams):
    ls.window_show_message(
        types.ShowMessageParams(
            message="Hello, world!",
            type=types.MessageType.Log,
        )
    )


if __name__ == "__main__":
    server.start_io()
