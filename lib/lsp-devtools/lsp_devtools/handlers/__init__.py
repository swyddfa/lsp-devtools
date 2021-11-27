import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union
from uuid import uuid4


class LspMessage:
    """A container that holds a message from the LSP protocol, with some additional metadata."""

    def __init__(
        self, session: str, timestamp: float, source: str, message: Dict[str, Any]
    ):
        self.session: str = session
        """An id representing the session the message is a part of."""

        self.timestamp: float = timestamp
        """When the message was sent (seconds since the epoch)."""

        self.source: str = source
        """Indicates if the message was sent by the client or the server."""

        self.message: Dict[str, Any] = message
        """The actual message sent over the lsp protocol."""

        self.id: Optional[str] = message.get("id", None)
        """The ``id`` field, if it exists."""

        self.method: Optional[str] = message.get("method", None)
        """The ``method`` field, if it exists."""

        # fmt: off
        self.params: Optional[Union[Dict[str, Any], List[Any]]] = message.get("params", None)
        """The ``params`` field, if it exists."""

        self.result: Optional[Union[Dict[str, Any], bool, float, str]] = message.get("result", None)
        """The ``result`` field, if it exists."""
        # fmt: on

        self.error: Optional[Dict[str, Any]] = message.get("error", None)
        """The ``error`` field, if it exists."""

    @property
    def is_request(self) -> bool:
        return self.id and self.params

    @property
    def is_response(self) -> bool:
        return self.id and (self.result or self.error)

    @property
    def is_notification(self) -> bool:
        return (not self.id) and self.params


class LspHandler(logging.Handler):
    """Base class for lsp log handlers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.session_id = None

    def handle_message(self, message: LspMessage):
        """Called each time a message is processed."""

    def emit(self, record: logging.LogRecord):

        message = record.args
        timestamp = record.created
        source = record.__dict__["source"]

        if message.get("method", None) == "initialize":
            self.session_id = str(uuid4())

        lsp_message = LspMessage(
            session=self.session_id, timestamp=timestamp, source=source, message=message
        )
        self.handle_message(lsp_message)
