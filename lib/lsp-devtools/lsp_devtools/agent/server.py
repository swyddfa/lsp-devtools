from pygls.protocol import default_converter
from pygls.server import Server

from lsp_devtools.agent.protocol import AgentProtocol


class AgentServer(Server):
    """A pygls server that wraps an agent allowing other processes to interact with it
    via websockets."""

    lsp: AgentProtocol

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            protocol_cls=AgentProtocol,
            converter_factory=default_converter,
            **kwargs
        )
