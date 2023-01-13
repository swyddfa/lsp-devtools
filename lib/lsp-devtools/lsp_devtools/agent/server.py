from pygls.protocol import default_converter
from pygls.server import Server

from lsp_devtools.agent.protocol import AgentProtocol


class AgentServer(Server):
    """A pygls server that wraps an agent allowing other processes to interact with it
    via websockets."""

    lsp: AgentProtocol

    def __init__(self, *args, **kwargs):

        if "protocol_cls" not in kwargs:
            kwargs["protocol_cls"] = AgentProtocol

        if "converter_factory" not in kwargs:
            kwargs["converter_factory"] = default_converter

        super().__init__(*args, **kwargs)
