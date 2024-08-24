# A server that exits mid request.
import sys

from lsprotocol import types
from pygls.lsp.server import LanguageServer


class CountingLanguageServer(LanguageServer):
    count: int = 0


server = CountingLanguageServer(name="completion-exit-server", version="v1.0")


@server.feature(types.TEXT_DOCUMENT_COMPLETION)
def on_complete(server: CountingLanguageServer, params: types.CompletionParams):
    server.count += 1
    if server.count == 5:
        sys.exit(0)

    return [types.CompletionItem(label=f"{server.count}")]


if __name__ == "__main__":
    server.start_io()
