# A server that exits mid request.
import sys

from lsprotocol.types import TEXT_DOCUMENT_COMPLETION
from lsprotocol.types import CompletionItem
from lsprotocol.types import CompletionParams
from pygls.server import LanguageServer


class CountingLanguageServer(LanguageServer):
    count: int = 0


server = CountingLanguageServer(name="completion-exit-server", version="v1.0")


@server.feature(TEXT_DOCUMENT_COMPLETION)
def on_complete(server: CountingLanguageServer, params: CompletionParams):
    server.count += 1
    if server.count == 5:
        sys.exit(0)

    return [CompletionItem(label=f"{server.count}")]


if __name__ == "__main__":
    server.start_io()
