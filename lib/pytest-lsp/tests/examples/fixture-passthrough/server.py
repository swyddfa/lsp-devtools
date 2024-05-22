from lsprotocol.types import TEXT_DOCUMENT_COMPLETION, CompletionItem, CompletionParams
from pygls.server import LanguageServer

server = LanguageServer("hello-world", "v1")


@server.feature(TEXT_DOCUMENT_COMPLETION)
def completion(ls: LanguageServer, params: CompletionParams):
    return [
        CompletionItem(label="hello"),
        CompletionItem(label="world"),
    ]


if __name__ == "__main__":
    server.start_io()
