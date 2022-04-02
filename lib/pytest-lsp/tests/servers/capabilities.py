from pygls.server import LanguageServer


server = LanguageServer()


@server.command("return.client.capabilities")
def on_initialize(ls: LanguageServer, *args):
    return ls.client_capabilities.dict(by_alias=False)


if __name__ == "__main__":
    server.start_io()
