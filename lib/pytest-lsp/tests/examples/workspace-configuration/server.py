from lsprotocol import types
from pygls.server import LanguageServer

server = LanguageServer("workspace-configuration", "v1")


@server.command("server.configuration")
async def configuration(ls: LanguageServer, *args):
    results = await ls.get_configuration_async(
        types.WorkspaceConfigurationParams(
            items=[
                types.ConfigurationItem(scope_uri="file://workspace/file.txt"),
                types.ConfigurationItem(section="not.found"),
                types.ConfigurationItem(section="values.c"),
            ]
        )
    )

    a = results[0]["values"]["a"]
    assert results[1] is None
    c = results[2]

    return a + c


if __name__ == "__main__":
    server.start_io()
