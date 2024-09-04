from lsprotocol.converters import get_converter
from pygls.lsp.server import LanguageServer

converter = get_converter()
server = LanguageServer(name="capabilities-server", version="v1.0")


@server.command("return.client.capabilities")
def on_initialize(ls: LanguageServer, *args):
    return ls.client_capabilities


if __name__ == "__main__":
    server.start_io()
