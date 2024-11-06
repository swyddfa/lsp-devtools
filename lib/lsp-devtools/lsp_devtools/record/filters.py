from __future__ import annotations

import logging
import typing

import attrs

from .formatters import FormatString

if typing.TYPE_CHECKING:
    from typing import Literal

    MessageSource = Literal["client", "server", "both"]
    MessageType = Literal["request", "response", "result", "error", "notification"]

logger = logging.getLogger(__name__)


@attrs.define
class LSPFilter(logging.Filter):
    """Logging filter for LSP messages."""

    message_source: MessageSource = attrs.field(default="both")
    """Only include messages from the given source."""

    include_message_types: set[MessageType] = attrs.field(factory=set, converter=set)
    """Only include the given message types."""

    exclude_message_types: set[MessageType] = attrs.field(factory=set, converter=set)
    """Exclude the given message types."""

    include_methods: set[str] = attrs.field(factory=set, converter=set)
    """Only include messages associated with the given method."""

    exclude_methods: set[str] = attrs.field(factory=set, converter=set)
    """Exclude messages associated with the given method."""

    formatter: FormatString = attrs.field(
        default="",
        converter=FormatString,
    )  # type: ignore
    """Format messages according to the given string"""

    _response_method_map: dict[int | str, str] = attrs.field(factory=dict)
    """Used to determine the method for response messages"""

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.args
        if not isinstance(message, dict):
            return False

        source = record.__dict__["Message-Source"]
        message_type = get_message_type(message)
        message_method = self._get_message_method(message_type, message)

        if self.message_source not in {"both", source}:
            return False

        if self.include_message_types and not message_matches_type(
            message_type, self.include_message_types
        ):
            return False

        if self.exclude_message_types and message_matches_type(
            message_type, self.exclude_message_types
        ):
            return False

        if self.include_methods and message_method not in self.include_methods:
            return False

        if self.exclude_methods and message_method in self.exclude_methods:
            return False

        if self.formatter.pattern:
            try:
                record.msg = self.formatter.format(message)
                record.args = None
            except Exception:
                logger.debug(
                    "Skipping message that failed to format: %s", message, exc_info=True
                )
                return False

        return True

    def _get_message_method(self, message_type: str, message: dict) -> str:
        if message_type == "request":
            method = message["method"]
            self._response_method_map[message["id"]] = method

            return method

        if message_type == "notification":
            return message["method"]

        return self._response_method_map[message["id"]]


def message_matches_type(message_type: str, types: set[MessageType]) -> bool:
    """Determine if the type of message is included in the given set of types"""

    if message_type == "result":
        return len({"result", "response"} & types) > 0

    if message_type == "error":
        return len({"error", "response"} & types) > 0

    return message_type in types


def get_message_type(message: dict) -> str:
    if "id" in message:
        if "error" in message:
            return "error"
        elif "method" in message:
            return "request"
        else:
            return "result"
    else:
        return "notification"
