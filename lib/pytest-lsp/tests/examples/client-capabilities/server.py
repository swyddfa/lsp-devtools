from lsprotocol.types import (
    TEXT_DOCUMENT_COMPLETION,
    CompletionItem,
    CompletionParams,
    InsertTextFormat,
)
from pygls.server import LanguageServer

server = LanguageServer("hello-world", "v1")


@server.feature(TEXT_DOCUMENT_COMPLETION)
def completion(ls: LanguageServer, params: CompletionParams):
    return [
        CompletionItem(
            label="greet",
            insert_text='"Hello, ${1:name}!"$0',
            insert_text_format=InsertTextFormat.Snippet,
        ),
    ]


if __name__ == "__main__":
    server.start_io()
