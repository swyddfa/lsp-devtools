from typing import Optional
from typing import Type

import attrs
from pygls.protocol import JsonRPCProtocol

MESSAGE_TEXT_NOTIFICATION = "message/text"


@attrs.define
class MessageText:
    """The contents of a ``message/text`` notification."""

    text: str
    """The captured text."""

    source: str
    """The source the text was captured from e.g. client."""


@attrs.define
class MessageTextNotification:
    """Notify the client of output that was captured by the agent."""

    jsonrpc: str
    method: str
    params: MessageText = attrs.field()


class AgentProtocol(JsonRPCProtocol):
    """The RPC protocol exposed by the agent."""

    def get_message_type(self, method: str) -> Optional[Type]:

        if method == MESSAGE_TEXT_NOTIFICATION:
            return MessageTextNotification

        return super().get_message_type(method)

    def message_text_notification(self, message: MessageText):
        """Send an ``message/text`` notification to the client."""
        self.notify(MESSAGE_TEXT_NOTIFICATION, message)
