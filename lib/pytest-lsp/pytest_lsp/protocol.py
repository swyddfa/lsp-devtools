import asyncio
import logging
from concurrent.futures import Future
from typing import Any

from lsprotocol.types import CANCEL_REQUEST
from pygls.exceptions import JsonRpcMethodNotFound
from pygls.protocol import LanguageServerProtocol

logger = logging.getLogger(__name__)


class LanguageClientProtocol(LanguageServerProtocol):
    """An extended protocol class with extra methods that are useful for testing."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._notification_futures = {}

    def _handle_notification(self, method_name, params):
        if method_name == CANCEL_REQUEST:
            self._handle_cancel_notification(params.id)
            return

        future = self._notification_futures.pop(method_name, None)
        if future:
            future.set_result(params)

        try:
            handler = self._get_handler(method_name)
            self._execute_notification(handler, params)
        except (KeyError, JsonRpcMethodNotFound):
            logger.warning("Ignoring notification for unknown method '%s'", method_name)
        except Exception:
            logger.exception(
                "Failed to handle notification '%s': %s", method_name, params
            )

    def send_request(self, method, params=None, callback=None, msg_id=None):
        def check_result(result: Any):
            logger.warn("%s", result)
            if callback:
                callback(result)

        return super().send_request(method, params, check_result, msg_id)

    def wait_for_notification(self, method: str, callback=None):
        future: Future = Future()
        if callback:

            def wrapper(future: Future):
                result = future.result()
                callback(result)

            future.add_done_callback(wrapper)

        self._notification_futures[method] = future
        return future

    def wait_for_notification_async(self, method: str):
        future = self.wait_for_notification(method)
        return asyncio.wrap_future(future)
