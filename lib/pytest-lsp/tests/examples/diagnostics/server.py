from lsprotocol import types
from pygls.lsp.server import LanguageServer

server = LanguageServer("diagnostic-server", "v1")


@server.feature(types.TEXT_DOCUMENT_DID_OPEN)
def did_open(ls: LanguageServer, params: types.DidOpenTextDocumentParams):
    ls.text_document_publish_diagnostics(
        types.PublishDiagnosticsParams(
            uri=params.text_document.uri,
            diagnostics=[
                types.Diagnostic(
                    message="There is an error here.",
                    range=types.Range(
                        start=types.Position(line=1, character=1),
                        end=types.Position(line=1, character=10),
                    ),
                )
            ],
        )
    )


if __name__ == "__main__":
    server.start_io()
