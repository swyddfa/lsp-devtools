"""Used for testing client's handling of return types."""
from pygls.lsp.methods import *
from pygls.lsp.types import *
from pygls.server import LanguageServer


server = LanguageServer()


def arange(spec: str) -> Range:

    start_line, start_char, end_line, end_char = [
        int(i) for item in spec.split("-") for i in item.split(":")
    ]

    return Range(
        start=Position(line=start_line, character=start_char),
        end=Position(line=end_line, character=end_char),
    )


@server.feature(COMPLETION)
def on_complete(ls: LanguageServer, params: CompletionParams):

    line = params.position.line

    if line == 0:
        return None

    if line == 1:
        return [CompletionItem(label="item-one"), CompletionItem(label="item-two")]

    return CompletionList(
        is_incomplete=True,
        items=[CompletionItem(label="item-a"), CompletionItem(label="item-b")],
    )


@server.feature(COMPLETION_ITEM_RESOLVE)
def on_complete_resolve(ls: LanguageServer, item: CompletionItem):
    item.documentation = "This is documented"
    return item


@server.feature(DEFINITION)
def on_definition(ls: LanguageServer, params: DefinitionParams):

    line = params.position.line

    if line == 0:
        return None

    if line == 1:
        return Location(uri=params.text_document.uri, range=arange("0:1-2:4"))

    if line == 2:
        return [
            Location(uri=params.text_document.uri, range=arange("0:1-2:4")),
            Location(uri=params.text_document.uri, range=arange("3:1-4:4")),
        ]

    return [
        LocationLink(
            target_uri=params.text_document.uri,
            target_range=arange("0:1-2:4"),
            target_selection_range=arange("3:1-4:4"),
        ),
    ]


@server.feature(DOCUMENT_LINK)
def on_document_link(ls: LanguageServer, params: DocumentLinkParams):

    doc = params.text_document.uri

    if doc.endswith("one.txt"):
        return None

    if doc.endswith("two.txt"):
        return [
            DocumentLink(range=arange("0:1-2:4")),
            DocumentLink(range=arange("3:1-4:4")),
        ]


@server.feature(DOCUMENT_SYMBOL)
def on_document_symbol(ls: LanguageServer, params: DocumentSymbolParams):

    doc = params.text_document.uri

    if doc.endswith("one.txt"):
        return None

    if doc.endswith("two.txt"):
        return [
            DocumentSymbol(
                name="one",
                kind=SymbolKind.String,
                range=arange("0:1-2:4"),
                selection_range=arange("0:1-2:4"),
            ),
            DocumentSymbol(
                name="two",
                kind=SymbolKind.String,
                range=arange("4:1-5:4"),
                selection_range=arange("5:1-6:4"),
            ),
        ]

    return [
        SymbolInformation(
            name="one",
            kind=SymbolKind.String,
            location=Location(
                uri=doc,
                range=arange("4:1-5:4"),
            ),
        )
    ]


@server.feature(HOVER)
def on_hover(ls: LanguageServer, params: HoverParams):

    line = params.position.line

    if line == 0:
        return None

    return Hover(
        contents=MarkupContent(kind=MarkupKind.PlainText, value="hover content")
    )


if __name__ == "__main__":
    server.start_io()
