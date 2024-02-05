import sys

from lsprotocol import types
from pygls.server import LanguageServer

server = LanguageServer("server-stderr", "v1")


@server.feature(types.TEXT_DOCUMENT_COMPLETION)
def completion(params: types.CompletionParams):
    items = []

    for i in range(10):
        print(f"Suggesting item {i}", file=sys.stderr, flush=True)
        items.append(types.CompletionItem(label=f"item-{i}"))

    return items


if __name__ == "__main__":
    server.start_io()
