from __future__ import annotations

from pygls.protocol import JsonRPCProtocol


class AgentProtocol(JsonRPCProtocol):
    """The RPC protocol exposed by the agent."""
