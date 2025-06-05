from lsprotocol import types
from pygls.lsp.server import LanguageServer

server = LanguageServer("add-client-method", "v1")


@server.feature(types.TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls: LanguageServer, params: types.DidOpenTextDocumentParams):
    await ls.workspace_diagnostic_refresh_async(None)


if __name__ == "__main__":
    server.start_io()
