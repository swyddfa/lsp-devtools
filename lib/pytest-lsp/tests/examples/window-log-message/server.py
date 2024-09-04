from lsprotocol import types
from pygls.lsp.server import LanguageServer

server = LanguageServer("window-log-message", "v1")


@server.feature(types.TEXT_DOCUMENT_COMPLETION)
def completion(ls: LanguageServer, params: types.CompletionParams):
    items = []

    for i in range(10):
        ls.window_log_message(
            types.LogMessageParams(
                message=f"Suggesting item {i}", type=types.MessageType.Log
            )
        )
        items.append(types.CompletionItem(label=f"item-{i}"))

    return items


if __name__ == "__main__":
    server.start_io()
