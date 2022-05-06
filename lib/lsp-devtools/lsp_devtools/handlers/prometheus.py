from prometheus_client import Counter  # type: ignore
from prometheus_client import Histogram  # type: ignore
from prometheus_client import start_http_server  # type: ignore

from lsp_devtools.handlers import LspHandler
from lsp_devtools.handlers import LspMessage

REQUESTS_COUNTER = Counter(
    "lsp_request_count", "Number of requests sent.", ["session", "source", "method"]
)
REQUESTS_DURATION = Histogram(
    "lsp_request_duration",
    "Time it takes to process a request",
    ["session", "source", "method"],
)
NOTIFICATIONS_COUNTER = Counter(
    "lsp_notification_count",
    "Number of notification sent.",
    ["session", "source", "method"],
)


class PrometheusHandler(LspHandler):
    """Logging handler that exports metrics to prometheus."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        start_http_server(8010)

        self.pending_requests = {}

    def handle_message(self, message: LspMessage):

        if message.is_request:
            REQUESTS_COUNTER.labels(
                message.session, message.source, message.method
            ).inc()
            self.pending_requests[message.id] = message

        if message.is_response:
            request = self.pending_requests.get(message.id, None)
            if request:
                REQUESTS_DURATION.labels(
                    request.session, request.source, request.method
                ).observe(message.timestamp - request.timestamp)

        if message.is_notification:
            NOTIFICATIONS_COUNTER.labels(
                message.session, message.source, message.method
            ).inc()
