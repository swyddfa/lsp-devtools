from __future__ import annotations

import pytest

from lsp_devtools.agent import JsonRPCHandler
from lsp_devtools.agent import JsonRPCMessage
from lsp_devtools.agent import MessageSource
from lsp_devtools.agent.server import ParserState


@pytest.mark.parametrize(
    "start_state,data,end_state,messages",
    [
        # Test the basics
        pytest.param(ParserState(), b"", ParserState(), [], id="feed-empty"),
        pytest.param(
            ParserState(),
            b"Content",
            ParserState(bytearray(b"Content")),
            [],
            id="feed-simple",
        ),
        pytest.param(
            ParserState(bytearray(b"Content")),
            b"-Length: 3\r",
            ParserState(bytearray(b"Content-Length: 3\r")),
            [],
            id="feed-cr",
        ),
        pytest.param(
            ParserState(bytearray(b"Content-Length: 3\r")),
            b"\n",
            ParserState(bytearray(b""), headers={"Content-Length": "3"}),
            [],
            id="feed-nl",
        ),
        pytest.param(
            ParserState(bytearray(b""), headers={"Content-Length": "3"}),
            b"\r\n",
            ParserState(
                bytearray(b""), headers={"Content-Length": "3"}, headers_complete=True
            ),
            [],
            id="feed-crnl",
        ),
        pytest.param(
            ParserState(
                bytearray(b""), headers={"Content-Length": "3"}, headers_complete=True
            ),
            b"{ }Content-",
            ParserState(bytearray(b"Content-")),
            [JsonRPCMessage(headers={"Content-Length": "3"}, body={}, metadata={})],
            id="feed-body",
        ),
        # What if there is more than one header available at once?
        pytest.param(
            ParserState(),
            b"Content-Type: application/json\r\nContent-Length: 3\r\n",
            ParserState(
                headers={
                    "Content-Type": "application/json",
                    "Content-Length": "3",
                }
            ),
            [],
            id="feed-multi-header",
        ),
        pytest.param(
            ParserState(),
            b"Content-Type: application/json\r\nContent-Length: 3\r\n\r\n",
            ParserState(
                headers={
                    "Content-Type": "application/json",
                    "Content-Length": "3",
                },
                headers_complete=True,
            ),
            [],
            id="feed-header-end",
        ),
        # Or multiple complete messages?
        pytest.param(
            ParserState(),
            b"Content-Type: application/json\r\nContent-Length: 3\r\n\r\n{ }"
            b"Content-Length: 3\r\n\r\n{ }"
            b"Content-Length: 3\r\n",
            ParserState(
                headers={
                    "Content-Length": "3",
                },
                headers_complete=False,
            ),
            [
                JsonRPCMessage(
                    headers={"Content-Length": "3", "Content-Type": "application/json"},
                    body={},
                    metadata={},
                ),
                JsonRPCMessage(headers={"Content-Length": "3"}, body={}, metadata={}),
            ],
            id="feed-multi-message",
        ),
    ],
)
def test_jsonrpc_handler_feed(
    start_state: ParserState,
    data: bytes,
    end_state: ParserState,
    messages: list[JsonRPCMessage],
):
    """Ensure that the ``JsonRPCHandler`` can parse and emit messages correctly.

    Parameters
    ----------
    start_state
       The current state of the parser, before feeding it additional ``data``

    data
       The next sequence of bytes to send to the parser

    end_state
       The expected state of the parser, after feeding it addtional ``data``

    messages
       The expected list of messages the parser should have emitted.
    """

    class TestHandler(JsonRPCHandler):
        def __init__(self, start_state: ParserState):
            super().__init__()
            self.messages = []
            self._parsers[MessageSource.Client] = start_state

        def handle(self, message: JsonRPCMessage):
            self.messages.append(message)

    handler = TestHandler(start_state)
    handler.feed(data, MessageSource.Client)

    assert handler._parsers[MessageSource.Client] == end_state
    assert len(handler.messages) == len(messages)

    for expected, actual in zip(messages, handler.messages):
        assert expected.headers == actual.headers
        assert expected.body == actual.body
        # We'll ignore the metadata for now
