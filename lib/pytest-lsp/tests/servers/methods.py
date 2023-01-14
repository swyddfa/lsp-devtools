"""Used for testing client's handling of return types."""
from lsprotocol.types import COMPLETION_ITEM_RESOLVE
from lsprotocol.types import TEXT_DOCUMENT_COMPLETION
from lsprotocol.types import TEXT_DOCUMENT_DEFINITION
from lsprotocol.types import TEXT_DOCUMENT_DOCUMENT_LINK
from lsprotocol.types import TEXT_DOCUMENT_DOCUMENT_SYMBOL
from lsprotocol.types import TEXT_DOCUMENT_HOVER
from lsprotocol.types import TEXT_DOCUMENT_IMPLEMENTATION
from lsprotocol.types import CompletionItem
from lsprotocol.types import CompletionList
from lsprotocol.types import CompletionParams
from lsprotocol.types import DefinitionParams
from lsprotocol.types import DocumentLink
from lsprotocol.types import DocumentLinkParams
from lsprotocol.types import DocumentSymbol
from lsprotocol.types import DocumentSymbolParams
from lsprotocol.types import Hover
from lsprotocol.types import HoverParams
from lsprotocol.types import ImplementationParams
from lsprotocol.types import Location
from lsprotocol.types import LocationLink
from lsprotocol.types import MarkupContent
from lsprotocol.types import MarkupKind
from lsprotocol.types import Position
from lsprotocol.types import Range
from lsprotocol.types import SymbolInformation
from lsprotocol.types import SymbolKind
from pygls.server import LanguageServer

server = LanguageServer(name="methods-server", version="v1.0")


def arange(spec: str) -> Range:

    start_line, start_char, end_line, end_char = (
        int(i) for item in spec.split("-") for i in item.split(":")
    )

    return Range(
        start=Position(line=start_line, character=start_char),
        end=Position(line=end_line, character=end_char),
    )


@server.feature(TEXT_DOCUMENT_COMPLETION)
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


@server.feature(TEXT_DOCUMENT_DEFINITION)
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


@server.feature(TEXT_DOCUMENT_DOCUMENT_LINK)
def on_document_link(ls: LanguageServer, params: DocumentLinkParams):

    doc = params.text_document.uri

    if doc.endswith("one.txt"):
        return None

    if doc.endswith("two.txt"):
        return [
            DocumentLink(range=arange("0:1-2:4")),
            DocumentLink(range=arange("3:1-4:4")),
        ]


@server.feature(TEXT_DOCUMENT_DOCUMENT_SYMBOL)
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


@server.feature(TEXT_DOCUMENT_HOVER)
def on_hover(ls: LanguageServer, params: HoverParams):

    line = params.position.line

    if line == 0:
        return None

    return Hover(
        contents=MarkupContent(kind=MarkupKind.PlainText, value="hover content")
    )


@server.feature(TEXT_DOCUMENT_IMPLEMENTATION)
def on_implementation(ls: LanguageServer, params: ImplementationParams):

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


if __name__ == "__main__":
    server.start_io()
