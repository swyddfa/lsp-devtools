import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Mapping
from typing import Optional
from typing import Union
from uuid import uuid4

LspParams = Union[Dict[str, Any], List[Any]]
LspResult = Union[Dict[str, Any], bool, float, str]


class LspMessage:
    """A container that holds a message from the LSP protocol, with some additional metadata."""

    def __init__(
        self, session: str, timestamp: float, source: str, message: Mapping[str, object]
    ):
        self.session: str = session
        """An id representing the session the message is a part of."""

        self.timestamp: float = timestamp
        """When the message was sent (seconds since the epoch)."""

        self.source: str = source
        """Indicates if the message was sent by the client or the server."""

        self.message: Mapping[str, object] = message
        """The actual message sent over the lsp protocol."""

        self.id: Optional[str] = message.get("id", None)  # type: ignore
        """The ``id`` field, if it exists."""

        self.method: Optional[str] = message.get("method", None)  # type: ignore
        """The ``method`` field, if it exists."""

        self.params: Optional[LspParams] = message.get("params", None)  # type: ignore
        """The ``params`` field, if it exists."""

        self.result: Optional[LspResult] = message.get("result", None)  # type: ignore
        """The ``result`` field, if it exists."""

        self.error: Optional[Dict[str, Any]] = message.get("error", None)  # type: ignore
        """The ``error`` field, if it exists."""

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

        self.session_id = None

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

        lsp_message = LspMessage(
            session=self.session_id, timestamp=timestamp, source=source, message=message
        )
        self.handle_message(lsp_message)
