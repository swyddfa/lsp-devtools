# A server that exits mid request.
import sys

from lsprotocol.types import TEXT_DOCUMENT_COMPLETION
from lsprotocol.types import CompletionItem
from lsprotocol.types import CompletionParams
from pygls.server import LanguageServer

count = 0
server = LanguageServer(name="completion-exit-server", version="v1.0")


@server.feature(TEXT_DOCUMENT_COMPLETION)
def on_complete(server: LanguageServer, params: CompletionParams):

    count += 1
    if count == 5:
        sys.exit(0)

    return [CompletionItem(label=f"{count}")]

