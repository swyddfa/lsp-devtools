from lsprotocol import types
from pygls.lsp.server import LanguageServer

server = LanguageServer("window-show-document", "v1")


@server.feature(types.TEXT_DOCUMENT_COMPLETION)
async def completion(ls: LanguageServer, params: types.CompletionParams):
    items = []
    await ls.window_show_document_async(
        types.ShowDocumentParams(uri=params.text_document.uri)
    )

    for i in range(10):
        items.append(types.CompletionItem(label=f"item-{i}"))

    return items


if __name__ == "__main__":
    server.start_io()
