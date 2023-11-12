from unittest.mock import Mock

from lsprotocol import types
from pygls.server import LanguageServer

server = LanguageServer("window-create-progress", "v1")


@server.command("do.progress")
async def do_progress(ls: LanguageServer, *args):
    token = "a-token"

    await ls.progress.create_async(token)

    # Begin
    ls.progress.begin(
        token,
        types.WorkDoneProgressBegin(title="Indexing", percentage=0),
    )
    # Report
    for i in range(1, 4):
        ls.progress.report(
            token,
            types.WorkDoneProgressReport(message=f"{i * 25}%", percentage=i * 25),
        )
    # End
    ls.progress.end(token, types.WorkDoneProgressEnd(message="Finished"))

    return "a result"


@server.command("duplicate.progress")
async def duplicate_progress(ls: LanguageServer, *args):
    token = "duplicate-token"

    # Need to stop pygls preventing us from using the progress API wrong.
    ls.progress._check_token_registered = Mock()
    await ls.progress.create_async(token)

    # pytest-lsp should return an error here.
    await ls.progress.create_async(token)


@server.command("no.progress")
async def no_progress(ls: LanguageServer, *args):
    token = "undefined-token"

    # Begin
    ls.progress.begin(
        token,
        types.WorkDoneProgressBegin(title="Indexing", percentage=0, cancellable=False),
    )
    # Report
    for i in range(1, 4):
        ls.progress.report(
            token,
            types.WorkDoneProgressReport(message=f"{i * 25}%", percentage=i * 25),
        )
    # End
    ls.progress.end(token, types.WorkDoneProgressEnd(message="Finished"))


if __name__ == "__main__":
    server.start_io()
