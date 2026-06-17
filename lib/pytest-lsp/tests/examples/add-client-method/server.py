from lsprotocol import types
from pygls.lsp.server import LanguageServer

server = LanguageServer("add-client-method", "v1")


@server.feature(types.TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls: LanguageServer, params: types.DidOpenTextDocumentParams):
    await ls.protocol.send_request_async("custom/myMethod", None)


if __name__ == "__main__":
    server.start_io()
