from lsprotocol.types import (
    TEXT_DOCUMENT_COMPLETION,
    CompletionItem,
    CompletionParams,
    ShowDocumentParams,
)
from pygls.server import LanguageServer

server = LanguageServer("window-show-document", "v1")


@server.feature(TEXT_DOCUMENT_COMPLETION)
async def completion(ls: LanguageServer, params: CompletionParams):
    items = []
    await ls.show_document_async(ShowDocumentParams(uri=params.text_document.uri))

    for i in range(10):
        items.append(CompletionItem(label=f"item-{i}"))

    return items


if __name__ == "__main__":
    server.start_io()
