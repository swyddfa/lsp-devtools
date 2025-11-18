from __future__ import annotations

import logging
import typing

import attrs

from lsp_devtools.agent import MessageSource

if typing.TYPE_CHECKING:
    from typing import Literal

    from lsp_devtools.handlers.jsonrpc import JsonRPCMessage
    from lsp_devtools.handlers.jsonrpc import JsonRPCMessageType

    MessageSourceString = Literal["client", "server", "both"]


logger = logging.getLogger(__name__)


def string_to_message_source(
    value: MessageSourceString | MessageSource,
) -> Literal["both"] | MessageSource:
    if value == "both":
        return "both"

    if value == "client":
        return MessageSource.CLIENT

    if value == "server":
        return MessageSource.SERVER

    return value


@attrs.define
class JsonRPCFilter:
    """Logging filter for JSON-RPC messages."""

    message_source: Literal["both"] | MessageSource = attrs.field(
        default="both", converter=string_to_message_source
    )
    """Only include messages from the given source."""

    include_message_types: set[JsonRPCMessageType] = attrs.field(
        factory=set, converter=set
    )
    """Only include the given message types."""

    exclude_message_types: set[JsonRPCMessageType] = attrs.field(
        factory=set, converter=set
    )
    """Exclude the given message types."""

    include_methods: set[str] = attrs.field(factory=set, converter=set)
    """Only include messages associated with the given method."""

    exclude_methods: set[str] = attrs.field(factory=set, converter=set)
    """Exclude messages associated with the given method."""

    _response_method_map: dict[int | str, str] = attrs.field(factory=dict)
    """Used to determine the method for response messages"""

    def match(self, message: JsonRPCMessage) -> JsonRPCMessage | None:
        """Return the given message if it passes the configured filters"""
        source = message.metadata["source"]
        message_type = message.msg_type
        message_method = self._get_message_method(message)

        if not self.source_matches(source):
            return None

        if self.include_message_types and not message_matches_type(
            message_type, self.include_message_types
        ):
            return None

        if self.exclude_message_types and message_matches_type(
            message_type, self.exclude_message_types
        ):
            return None

        if self.include_methods and message_method not in self.include_methods:
            return None

        if self.exclude_methods and message_method in self.exclude_methods:
            return None

        return message

    def source_matches(self, source: MessageSource):
        if source == MessageSource.AGENT:
            return False

        return self.message_source in {"both", source}

    def _get_message_method(self, message: JsonRPCMessage) -> str | None:
        method = message.method
        msg_id = message.msg_id

        if message.msg_type in {"request", "notification"}:
            if msg_id is not None and method is not None:
                self._response_method_map[msg_id] = method

            return method

        if msg_id is not None:
            return self._response_method_map.get(msg_id)

        return None


def message_matches_type(message_type: str, types: set[JsonRPCMessageType]) -> bool:
    """Determine if the type of message is included in the given set of types"""

    if message_type == "result":
        return len({"result", "response"} & types) > 0

    if message_type == "error":
        return len({"error", "response"} & types) > 0

    return message_type in types
