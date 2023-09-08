from pygls.protocol import JsonRPCProtocol, default_converter
from pygls.server import Server

server = Server(protocol_cls=JsonRPCProtocol, converter_factory=default_converter)


@server.lsp.fm.feature("math/add")
def addition(ls: Server, params):
    a = params.a
    b = params.b

    ls.lsp.notify("log/message", dict(message=f"{a=}"))
    ls.lsp.notify("log/message", dict(message=f"{b=}"))

    return dict(total=a + b)


@server.lsp.fm.feature("math/sub")
def subtraction(ls: Server, params):
    a = params.a
    b = params.b

    ls.lsp.notify("log/message", dict(message=f"{a=}"))
    ls.lsp.notify("log/message", dict(message=f"{b=}"))

    return dict(total=b - a)


if __name__ == "__main__":
    server.start_io()
