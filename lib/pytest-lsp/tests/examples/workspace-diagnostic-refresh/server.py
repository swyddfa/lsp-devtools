from pygls.lsp.server import LanguageServer

server = LanguageServer("workspace-configuration", "v1")


@server.command("server.diagnostics")
async def diagnostics(ls: LanguageServer, do_refresh: bool):
    if do_refresh:
        await ls.workspace_diagnostic_refresh_async(None)


if __name__ == "__main__":
    server.start_io()
