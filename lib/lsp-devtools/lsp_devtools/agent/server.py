import json
import re
from typing import Any
from typing import Callable
from typing import Optional

from pygls.protocol import default_converter
from pygls.server import Server

from lsp_devtools.agent.protocol import AgentProtocol
from lsp_devtools.agent.protocol import MessageText


class AgentServer(Server):
    """A pygls server that accepts connections from agents allowing them to send their
    collected messages."""

    lsp: AgentProtocol

    def __init__(self, *args, **kwargs):
        if "protocol_cls" not in kwargs:
            kwargs["protocol_cls"] = AgentProtocol

        if "converter_factory" not in kwargs:
            kwargs["converter_factory"] = default_converter

        super().__init__(*args, **kwargs)
        self._client_buffer = []
        self._server_buffer = []

    def feature(self, feature_name: str, options: Optional[Any] = None):
        return self.lsp.fm.feature(feature_name, options)


MESSAGE_PATTERN = re.compile(
    r"^(?:[^\r\n]+\r\n)*"
    + r"Content-Length: (?P<length>\d+)\r\n"
    + r"(?:[^\r\n]+\r\n)*\r\n"
    + r"(?P<body>{.*)",
    re.DOTALL,
)


def parse_rpc_message(
    ls: AgentServer, message: MessageText, callback: Callable[[dict], None]
):
    """Parse json-rpc messages coming from the agent.

    Originally adatped from the ``data_received`` method on pygls' ``JsonRPCProtocol``
    class.
    """
    data = message.text
    message_buf = ls._client_buffer if message.source == "client" else ls._server_buffer

    while len(data):
        # Append the incoming chunk to the message buffer
        message_buf.append(data)

        # Look for the body of the message
        msg = "".join(message_buf)
        found = MESSAGE_PATTERN.fullmatch(msg)

        body = found.group("body") if found else ""
        length = int(found.group("length")) if found else 1

        if len(body) < length:
            # Message is incomplete; bail until more data arrives
            return

        # Message is complete;
        # extract the body and any remaining data,
        # and reset the buffer for the next message
        body, data = body[:length], body[length:]
        message_buf.clear()

        callback(json.loads(body))
