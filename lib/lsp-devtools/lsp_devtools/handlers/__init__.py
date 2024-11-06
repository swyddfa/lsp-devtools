from __future__ import annotations

import json
import logging
import typing
from datetime import datetime

import attrs

if typing.TYPE_CHECKING:
    from collections.abc import Mapping
    from typing import Any
    from typing import Literal

    MessageSource = Literal["client", "server"]


def maybe_json(value):
    try:
        return json.loads(value)
    except Exception:
        return value


@attrs.define
class LspMessage:
    """A container that holds a message from the LSP protocol, with some additional
    metadata."""

    session: str
    """An id representing the session the message is a part of."""

    timestamp: datetime
    """When the message was sent."""

    source: MessageSource
    """Indicates if the message was sent by the client or the server."""

    id: str | None
    """The ``id`` field, if it exists."""

    method: str | None
    """The ``method`` field, if it exists."""

    params: Any | None = attrs.field(converter=maybe_json)
    """The ``params`` field, if it exists."""

    result: Any | None = attrs.field(converter=maybe_json)
    """The ``result`` field, if it exists."""

    error: Any | None = attrs.field(converter=maybe_json)
    """The ``error`` field, if it exists."""

    @classmethod
    def from_rpc(
        cls, session: str, timestamp: str, source: str, message: Mapping[str, Any]
    ):
        """Create an instance from a JSON-RPC message."""
        return cls(
            session=session,
            timestamp=datetime.fromisoformat(timestamp),
            source=source,  # type: ignore
            id=message.get("id", None),
            method=message.get("method", None),
            params=message.get("params", None),
            result=message.get("result", None),
            error=message.get("error", None),
        )

    @property
    def is_request(self) -> bool:
        return self.id is not None and self.params is not None

    @property
    def is_response(self) -> bool:
        result_or_error = self.result is not None or self.error is not None
        return self.id is not None and result_or_error

    @property
    def is_notification(self) -> bool:
        return self.id is None and self.params is not None


class LspHandler(logging.Handler):
    """Base class for lsp log handlers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def handle_message(self, message: LspMessage):
        """Called each time a message is processed."""

    def emit(self, record: logging.LogRecord):
        if not isinstance(record.args, dict):
            return

        message = record.args
        source = record.__dict__["Message-Source"]

        self.handle_message(
            LspMessage.from_rpc(
                session=record.__dict__["Message-Session"],
                timestamp=record.__dict__["Message-Timestamp"],
                source=source,
                message=message,
            )
        )
