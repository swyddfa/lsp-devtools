# A server that makes an unknown request.

from lsprotocol import types
from pygls.lsp.server import LanguageServer

server = LanguageServer(name="unknown-method-server", version="v1.0")


@server.feature(types.TEXT_DOCUMENT_COMPLETION)
async def on_complete(server: LanguageServer, params: types.CompletionParams):
    try:
        await server.protocol.send_request_async("unknown/method", {})
    except Exception:
        # We are interested in how the client handles unexpected messages and so the server should just continue.
        pass

    return [types.CompletionItem(label="one")]


if __name__ == "__main__":
    server.start_io()
