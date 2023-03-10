# A server that returns a message that cannot be parsed as JSON.
import json

from lsprotocol.types import TEXT_DOCUMENT_COMPLETION
from lsprotocol.types import CompletionItem
from lsprotocol.types import CompletionParams
from pygls.server import LanguageServer

server = LanguageServer(name="completion-exit-server", version="v1.0")


def bad_send_data(data):
    """Sends data to the client in a way that cannot be parsed."""
    if not data:
        return

    self = server.lsp
    body = json.dumps(data, default=self._serialize_message)
    body = body.replace('"', "'").encode(self.CHARSET)
    header = (
        f"Content-Length: {len(body)}\r\n"
        f"Content-Type: {self.CONTENT_TYPE}; charset={self.CHARSET}\r\n\r\n"
    ).encode(self.CHARSET)

    self.transport.write(header + body)


@server.feature(TEXT_DOCUMENT_COMPLETION)
def on_complete(server: LanguageServer, params: CompletionParams):
    server.lsp._send_data = bad_send_data
    return [CompletionItem(label="item-one")]


if __name__ == "__main__":
    server.start_io()
