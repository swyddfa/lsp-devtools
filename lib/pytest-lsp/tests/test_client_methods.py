import asyncio
import pathlib
import sys

import pygls.uris as uri
import pytest
import pytest_lsp
from lsprotocol.types import CompletionItem
from lsprotocol.types import CompletionList
from lsprotocol.types import DocumentLink
from lsprotocol.types import DocumentSymbol
from lsprotocol.types import Hover
from lsprotocol.types import Location
from lsprotocol.types import LocationLink
from lsprotocol.types import MarkupContent
from lsprotocol.types import MarkupKind
from lsprotocol.types import Position
from lsprotocol.types import Range
from lsprotocol.types import SymbolInformation
from lsprotocol.types import SymbolKind
from pytest_lsp import ClientServerConfig
from pytest_lsp import LanguageClient

ROOT_URI: str = uri.from_fs_path(str(pathlib.Path(__file__).parent))  # type: ignore
TEST_URI = f"{ROOT_URI}/text.txt"


def arange(spec: str) -> Range:
    start_line, start_char, end_line, end_char = (
        int(i) for item in spec.split("-") for i in item.split(":")
    )

    return Range(
        start=Position(line=start_line, character=start_char),
        end=Position(line=end_line, character=end_char),
    )


@pytest.fixture(scope="session")
def event_loop():
    # We need to redefine the event_loop fixture to match the scope of our
    # client_server fixture.
    #
    # https://github.com/pytest-dev/pytest-asyncio/issues/68#issuecomment-334083751

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_lsp.fixture(
    scope="session",
    config=ClientServerConfig(
        client="visual_studio_code",
        server_command=[
            sys.executable,
            str(pathlib.Path(__file__).parent / "servers" / "methods.py"),
        ],
        root_uri=ROOT_URI,
    ),
)
async def client(client_):
    ...


@pytest.mark.parametrize(
    "line,expected",
    [
        (0, None),
        (1, [CompletionItem(label="item-one"), CompletionItem(label="item-two")]),
        (
            2,
            CompletionList(
                is_incomplete=True,
                items=[CompletionItem(label="item-a"), CompletionItem(label="item-b")],
            ),
        ),
    ],
)
async def test_client_completion(client: LanguageClient, line: int, expected):
    """Ensure that the client can handle completion responses correctly"""

    response = await client.completion_request(TEST_URI, line, 0)
    assert response == expected


async def test_client_completion_resolve(client: LanguageClient):
    """Ensure that the client can handle completion resolve responses correctly"""

    item = CompletionItem(label="item-one")
    response = await client.completion_item_resolve_request(item)

    assert response.documentation == "This is documented"


@pytest.mark.parametrize(
    "line,expected",
    [
        (0, None),
        (1, Location(uri=TEST_URI, range=arange("0:1-2:4"))),
        (
            2,
            [
                Location(uri=TEST_URI, range=arange("0:1-2:4")),
                Location(uri=TEST_URI, range=arange("3:1-4:4")),
            ],
        ),
        (
            3,
            [
                LocationLink(
                    target_uri=TEST_URI,
                    target_range=arange("0:1-2:4"),
                    target_selection_range=arange("3:1-4:4"),
                ),
            ],
        ),
    ],
)
async def test_client_definition(client: LanguageClient, line: int, expected):
    """Ensure that the client can handle definition responses correctly"""

    response = await client.definition_request(TEST_URI, line=line, character=0)

    assert response == expected


@pytest.mark.parametrize(
    "uri,expected",
    [
        (f"{ROOT_URI}/one.txt", None),
        (
            f"{ROOT_URI}/two.txt",
            [
                DocumentLink(range=arange("0:1-2:4")),
                DocumentLink(range=arange("3:1-4:4")),
            ],
        ),
    ],
)
async def test_client_document_link(client: LanguageClient, uri: str, expected):
    """Ensure that the client can handle document link responses correctly"""

    response = await client.document_link_request(uri)
    assert response == expected


@pytest.mark.parametrize(
    "uri,expected",
    [
        (f"{ROOT_URI}/one.txt", None),
        (
            f"{ROOT_URI}/two.txt",
            [
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
            ],
        ),
        (
            f"{ROOT_URI}/three.txt",
            [
                SymbolInformation(
                    name="one",
                    kind=SymbolKind.String,
                    location=Location(
                        uri=f"{ROOT_URI}/three.txt",
                        range=arange("4:1-5:4"),
                    ),
                )
            ],
        ),
    ],
)
async def test_client_document_symbol(client: LanguageClient, uri: str, expected):
    """Ensure that the client can handle document symbol responses correctly"""

    response = await client.document_symbols_request(uri)
    assert response == expected


@pytest.mark.parametrize(
    "line,expected",
    [
        (0, None),
        (
            1,
            Hover(
                contents=MarkupContent(kind=MarkupKind.PlainText, value="hover content")
            ),
        ),
    ],
)
async def test_client_hover(client: LanguageClient, line: int, expected):
    """Ensure that the client can handle hover responses correctly"""

    response = await client.hover_request(TEST_URI, line=line, character=0)
    assert response == expected


@pytest.mark.parametrize(
    "line,expected",
    [
        (0, None),
        (1, Location(uri=TEST_URI, range=arange("0:1-2:4"))),
        (
            2,
            [
                Location(uri=TEST_URI, range=arange("0:1-2:4")),
                Location(uri=TEST_URI, range=arange("3:1-4:4")),
            ],
        ),
        (
            3,
            [
                LocationLink(
                    target_uri=TEST_URI,
                    target_range=arange("0:1-2:4"),
                    target_selection_range=arange("3:1-4:4"),
                ),
            ],
        ),
    ],
)
async def test_client_implementation(client: LanguageClient, line: int, expected):
    """Ensure that the client can handle implementation responses correctly"""

    response = await client.implementation_request(TEST_URI, line=line, character=0)

    assert response == expected
