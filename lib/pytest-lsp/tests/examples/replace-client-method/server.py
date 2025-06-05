from lsprotocol import types
from pygls.lsp.server import LanguageServer

server = LanguageServer("replace-client-method", "v1")


@server.feature(types.TEXT_DOCUMENT_DID_OPEN)
def did_open(ls: LanguageServer, params: types.DidOpenTextDocumentParams):
    ls.text_document_publish_diagnostics(
        types.PublishDiagnosticsParams(
            uri=params.text_document.uri,
            diagnostics=[],
            version=params.text_document.version,
        )
    )


if __name__ == "__main__":
    server.start_io()
