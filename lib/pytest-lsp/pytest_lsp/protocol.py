from __future__ import annotations

import asyncio
import logging
import typing
from concurrent.futures import Future

from pygls.protocol import LanguageServerProtocol

from .checks import check_params_against_client_capabilities
from .checks import check_result_against_client_capabilities

if typing.TYPE_CHECKING:
    from .client import LanguageClient


logger = logging.getLogger(__name__)


class LanguageClientProtocol(LanguageServerProtocol):
    """An extended protocol class adding functionality useful for testing."""

    _server: LanguageClient  # type: ignore[assignment]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._notification_futures = {}

    def _handle_request(self, msg_id, method_name, params):
        """Wrap pygls' handle_request implementation. This will

        - Check if the request from the server is compatible with the client's stated
          capabilities.

        """
        check_params_against_client_capabilities(
            self._server.capabilities, method_name, params
        )
        return super()._handle_request(msg_id, method_name, params)

    def _handle_notification(self, method_name, params):
        """Wrap pygls' handle_notification implementation. This will

        - Notify a future waiting on the notification, if applicable.

        - Check the params to see if they are compatible with the client's stated
          capabilities.

        """
        future = self._notification_futures.pop(method_name, None)
        if future:
            future.set_result(params)

        super()._handle_notification(method_name, params)

    async def send_request_async(self, method, params=None):
        """Wrap pygls' ``send_request_async`` implementation. This will

        - Check the params to see if they're compatible with the client's stated
          capabilities
        - Check the result to see if it's compatible with the client's stated
          capabilities

        Parameters
        ----------
        method
           The method name of the request to send

        params
           The associated parameters to go with the request

        Returns
        -------
        Any
           The result
        """
        check_params_against_client_capabilities(
            self._server.capabilities, method, params
        )
        result = await super().send_request_async(method, params)
        check_result_against_client_capabilities(
            self._server.capabilities,
            method,
            result,  # type: ignore
        )

        return result

    def wait_for_notification(self, method: str, callback=None) -> Future:
        """Wait for a notification message with the given ``method``.

        Parameters
        ----------
        method
           The method name to wait for

        callback
           If given, ``callback`` will be called with the notification message's
           ``params`` when recevied

        Returns
        -------
        Future
           A future that will resolve when the requested notification message is
          recevied.
        """
        future: Future = Future()
        if callback:

            def wrapper(future: Future):
                result = future.result()
                callback(result)

            future.add_done_callback(wrapper)

        self._notification_futures[method] = future
        return future

    def wait_for_notification_async(self, method: str):
        """Wait for a notification message with the given ``method``.

        Parameters
        ----------
        method
           The method name to wait for

        Returns
        -------
        Any
           The notification message's ``params``
        """
        future = self.wait_for_notification(method)
        return asyncio.wrap_future(future)
