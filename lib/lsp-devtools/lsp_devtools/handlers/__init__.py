import logging
from typing import Any
from typing import Literal
from typing import Mapping
from typing import Optional
from uuid import uuid4

import attrs

MessageSource = Literal["client", "server"]


@attrs.define
class LspMessage:
    """A container that holds a message from the LSP protocol, with some additional
    metadata."""

    Source = MessageSource

    session: str
    """An id representing the session the message is a part of."""

    timestamp: float
    """When the message was sent."""

    source: MessageSource
    """Indicates if the message was sent by the client or the server."""

    id: Optional[str]
    """The ``id`` field, if it exists."""

    method: Optional[str]
    """The ``method`` field, if it exists."""

    params: Optional[Any]
    """The ``params`` field, if it exists."""

    result: Optional[Any]
    """The ``result`` field, if it exists."""

    error: Optional[Any]
    """The ``error`` field, if it exists."""

    @classmethod
    def from_rpc(
        cls, session: str, timestamp: float, source: str, message: Mapping[str, Any]
    ):
        """Create an instance from a JSON-RPC message."""
        return cls(
            session=session,
            timestamp=timestamp,
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
        self.session_id = ""

    def handle_message(self, message: LspMessage):
        """Called each time a message is processed."""

    def emit(self, record: logging.LogRecord):

        if not isinstance(record.args, dict):
            return

        message = record.args
        timestamp = record.created
        source = record.__dict__["source"]

        if message.get("method", None) == "initialize":
            self.session_id = str(uuid4())

        self.handle_message(
            LspMessage.from_rpc(
                session=self.session_id,
                timestamp=timestamp,
                source=source,
                message=message,
            )
        )
