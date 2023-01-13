import asyncio
import logging
import typing
from functools import partial

from textual.message import Message

from lsp_devtools.agent import MESSAGE_TEXT_NOTIFICATION
from lsp_devtools.agent import AgentClient
from lsp_devtools.agent import MessageText
from lsp_devtools.agent import parse_rpc_message
from lsp_devtools.record import logger
from lsp_devtools.record import setup_sqlite_output

if typing.TYPE_CHECKING:
    from . import LSPInspector


class Ping(Message):
    """Sent when the UI needs a refresh."""


class TUIAgentClient(AgentClient):
    def __init__(self, app: "LSPInspector"):
        self.app = app
        super().__init__()


def log_message(ls: TUIAgentClient, source: str, message: dict):
    logger.info("%s", message, extra={"source": source})
    app = ls.app

    # The event loop only becomes available once the on_ready event has fired
    # and the UI has bootstrapped itself. So it's possible we recevie
    # messages before the app is ready to accept them.
    if app.loop is None:
        return

    asyncio.run_coroutine_threadsafe(app.post_message(Ping(app)), app.loop)


def recv_message(ls: TUIAgentClient, message: MessageText):
    logfn = partial(log_message, ls, message.source)
    parse_rpc_message(ls, message, logfn)


def connect_to_agent(args, app: "LSPInspector"):
    client = TUIAgentClient(app)
    client.feature(MESSAGE_TEXT_NOTIFICATION)(recv_message)

    logger.setLevel(logging.INFO)
    setup_sqlite_output(args)

    return client
