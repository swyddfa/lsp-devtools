import importlib.resources as resources

from docutils import nodes
from docutils.parsers.rst import Directive
from packaging.version import parse as parse_version
from sphinx.application import Sphinx


class SupportedClients(Directive):
    def load_clients(self):
        clients = {}

        for resource in resources.files("pytest_lsp.clients").iterdir():
            # Skip the README or any other files that we don't care about.
            if not resource.name.endswith(".json"):
                continue

            client, version = resource.name.replace(".json", "").split("_v")
            client = " ".join([c.capitalize() for c in client.split("_")])

            clients.setdefault(client, []).append(version)

        return clients

    def run(self):
        rows = []
        clients = self.load_clients()

        for client, versions in clients.items():
            version_string = ", ".join(sorted(versions, key=parse_version))
            rows.append(
                nodes.row(
                    "",
                    nodes.entry(
                        "",
                        nodes.paragraph("", client),
                    ),
                    nodes.entry(
                        "",
                        nodes.paragraph("", version_string),
                    ),
                ),
            )

        header = nodes.row(
            "",
            nodes.entry(
                "",
                nodes.paragraph("", "Client"),
            ),
            nodes.entry(
                "",
                nodes.paragraph("", "Versions"),
            ),
        )

        table = nodes.table(
            "",
            nodes.tgroup(
                "",
                nodes.colspec("", colwidth="8"),
                nodes.colspec("", colwidth="4"),
                nodes.thead("", header),
                nodes.tbody("", *rows),
                cols=2,
            ),
        )

        return [table]


def setup(app: Sphinx):
    app.add_directive("supported-clients", SupportedClients)
