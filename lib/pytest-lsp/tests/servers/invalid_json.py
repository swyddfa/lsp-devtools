# A server that returns a message that cannot be parsed as JSON.
import json
import sys

from lsprotocol import types
from pygls.io_ import StdoutWriter
from pygls.lsp.server import LanguageServer

server = LanguageServer(name="completion-exit-server", version="v1.0")


def bad_send_data(data):
    """Sends data to the client in a way that cannot be parsed."""
    if not data:
        return

    self = server.protocol
    body = json.dumps(data, default=self._serialize_message)
    body = body.replace('"', "'").encode(self.CHARSET)
    header = (
        f"Content-Length: {len(body)}\r\n"
        f"Content-Type: {self.CONTENT_TYPE}; charset={self.CHARSET}\r\n\r\n"
    ).encode(self.CHARSET)

    self.writer.write(header + body)


@server.feature(types.TEXT_DOCUMENT_COMPLETION)
def on_complete(server: LanguageServer, params: types.CompletionParams):
    server.protocol._send_data = bad_send_data
    server.protocol.set_writer(StdoutWriter(sys.stdout.buffer))

    return [types.CompletionItem(label="item-one")]


if __name__ == "__main__":
    server.start_io()
