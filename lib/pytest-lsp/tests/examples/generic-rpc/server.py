import sys

from pygls.protocol import JsonRPCProtocol, default_converter
from pygls.server import JsonRPCServer

server = JsonRPCServer(
    protocol_cls=JsonRPCProtocol, converter_factory=default_converter
)


@server.feature("math/add")
def addition(ls: JsonRPCServer, params):
    a = params.a
    b = params.b

    ls.protocol.notify("log/message", dict(message=f"{a=}"))
    ls.protocol.notify("log/message", dict(message=f"{b=}"))

    return dict(total=a + b)


@server.feature("math/sub")
def subtraction(ls: JsonRPCServer, params):
    a = params.a
    b = params.b

    ls.protocol.notify("log/message", dict(message=f"{a=}"))
    ls.protocol.notify("log/message", dict(message=f"{b=}"))

    return dict(total=b - a)


@server.feature("server/exit")
def server_exit(ls: JsonRPCServer, params):
    sys.exit(0)


if __name__ == "__main__":
    server.start_io()
