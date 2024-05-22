from lsprotocol.types import (
    TEXT_DOCUMENT_DID_OPEN,
    Diagnostic,
    DidOpenTextDocumentParams,
    Position,
    Range,
)
from pygls.server import LanguageServer

server = LanguageServer("diagnostic-server", "v1")


@server.feature(TEXT_DOCUMENT_DID_OPEN)
def did_open(ls: LanguageServer, params: DidOpenTextDocumentParams):
    ls.publish_diagnostics(
        params.text_document.uri,
        [
            Diagnostic(
                message="There is an error here.",
                range=Range(
                    start=Position(line=1, character=1),
                    end=Position(line=1, character=10),
                ),
            )
        ],
    )


if __name__ == "__main__":
    server.start_io()
