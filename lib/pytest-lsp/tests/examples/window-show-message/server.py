from lsprotocol.types import TEXT_DOCUMENT_COMPLETION, CompletionItem, CompletionParams
from pygls.server import LanguageServer

server = LanguageServer("window-show-message", "v1")


@server.feature(TEXT_DOCUMENT_COMPLETION)
def completion(ls: LanguageServer, params: CompletionParams):
    items = []

    for i in range(10):
        ls.show_message(f"Suggesting item {i}")
        items.append(CompletionItem(label=f"item-{i}"))

    return items


if __name__ == "__main__":
    server.start_io()
