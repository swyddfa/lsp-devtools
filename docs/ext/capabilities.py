import importlib.resources as resources
import json
import pathlib
import re
import typing
from typing import Dict
from typing import List
from typing import Optional

import attrs
from docutils import nodes
from docutils.parsers.rst import directives
from lsprotocol import types
from lsprotocol.converters import get_converter
from packaging.version import parse as parse_version
from pygls.capabilities import get_capability
from sphinx.application import Sphinx
from sphinx.domains import Domain
from sphinx.pycode import ModuleAnalyzer
from sphinx.util.docutils import SphinxDirective


class BoolTable(SphinxDirective):
    """Given a boolean capability, indicate the support across known clients and
    versions"""

    required_arguments = 1

    option_spec = {
        "caption": directives.unchanged,
    }

    def build_header(self):
        columns = ["Client", "Supported Since"]
        colspecs = [nodes.colspec("", colwidth="1") for _ in range(len(columns))]
        header = nodes.thead(
            "",
            nodes.row("", *[nodes.entry("", nodes.Text(col)) for col in columns]),
        )

        return header, colspecs

    def get_client_support_for(self, capability: str) -> Dict[str, Optional[str]]:
        """Build a dictionary containing the clients that support the given capability
        as well as the version that support was introduced in."""
        domain = self.env.domains["capabilities"]

        clients: Dict[str, Optional[str]] = {}
        for (name, version), capabilities in domain.clients.items():
            supported = get_capability(capabilities, capability, False)

            if not supported:
                if name not in clients:
                    clients[name] = None
                continue

            if (existing := clients.get(name, None)) is None:
                clients[name] = version
            else:
                clients[name] = min(existing, version, key=parse_version)

        return clients

    def build_body(self, capability: str):
        rows = []
        clients = self.get_client_support_for(capability)

        for name, version in clients.items():
            rows.append(
                nodes.row(
                    "",
                    nodes.entry("", nodes.Text(name)),
                    nodes.entry(
                        "",
                        nodes.Text(version or " - "),
                        classes=["centered"],
                    ),
                )
            )

        return nodes.tbody("", *rows)

    def run(self):
        domain = self.env.domains["capabilities"]

        capability = self.arguments[0]
        if len(documentation := domain.get_capability_documentation(capability)) > 0:
            self.state_machine.insert_input(documentation, "<lsprotocol.types>")

        header, colspecs = self.build_header()
        body = self.build_body(capability)

        table = nodes.table("", nodes.tgroup("", *colspecs, header, body))

        if (caption := self.options.get("caption", None)) is not None:
            table.insert(0, nodes.title("", caption))

        paragraph = nodes.paragraph(
            "",
            nodes.Text("Capability: "),
            nodes.literal("", to_camel_case(capability)),
        )

        return [table, paragraph]


def to_camel_case(snake_text: str) -> str:
    """Convert snake_case to camelCase"""
    first, *remaining = snake_text.split("_")
    return first + "".join([text[0].upper() + text[1:] for text in remaining])


def _load_clients():
    """Load client capability data from pytest_lsp"""
    clients = {}
    converter = get_converter()

    for resource in resources.files("pytest_lsp.clients").iterdir():
        if not resource.name.endswith(".json"):
            continue

        capabilities = json.loads(pathlib.Path(resource).read_text())
        params = converter.structure(capabilities, types.InitializeParams)

        name = params.client_info.name
        version = params.client_info.version

        clients[(name, version)] = params.capabilities

    return clients


CODE_FENCE_PATTERN = re.compile(r"```(\w+)?")
LINK_PATTERN = re.compile(r"\{@link ([^}]+)\}")
LITERAL_PATTERN = re.compile(r"(?<![`:])`([^`]+)`(?!_)")
MD_LINK_PATTERN = re.compile(r"\[`?([^\]]+?)`?\]\(([^)]+)\)")
SINCE_PATTERN = re.compile(r"@since ([\d\.]+)")


def process_docstring(lines):
    """Fixup LSP docstrings so that they work with reStructuredText syntax

    - Replaces ``@since <version>`` with ``**LSP v<version>**``

    - Replaces ``{@link <item>}`` with ``:class:`~lsprotocol.types.<item>` ``

    - Replaces markdown hyperlink with reStructuredText equivalent

    - Replaces inline markdown code (single "`") with reStructuredText inline code
      (double "`")

    - Inserts the required newline before a bulleted list

    - Replaces code fences with code blocks

    - Fixes indentation
    """

    line_breaks = []
    code_fences = []

    for i, line in enumerate(lines):
        if line.startswith("- "):
            line_breaks.append(i)

        # Does the line need dedenting?
        if line.startswith(" " * 4) and not lines[i - 1].startswith(" "):
            # Be sure to modify the original list *and* the line the rest of the
            # loop will use.
            line = lines[i][4:]
            lines[i] = line

        if (match := SINCE_PATTERN.search(line)) is not None:
            start, end = match.span()
            lines[i] = "".join([line[:start], f"**LSP v{match.group(1)}**", line[end:]])

        if (match := LINK_PATTERN.search(line)) is not None:
            start, end = match.span()
            item = match.group(1)

            lines[i] = "".join(
                [line[:start], f":class:`~pygls:lsprotocol.types.{item}`", line[end:]]
            )

        if (match := MD_LINK_PATTERN.search(line)) is not None:
            start, end = match.span()
            text = match.group(1)
            target = match.group(2)

            line = "".join([line[:start], f"`{text} <{target}>`__", line[end:]])
            lines[i] = line

        if (match := LITERAL_PATTERN.search(line)) is not None:
            start, end = match.span()
            lines[i] = "".join([line[:start], f"`{match.group(0)}` ", line[end:]])

        if (match := CODE_FENCE_PATTERN.match(line)) is not None:
            open_ = len(code_fences) % 2 == 0
            lang = match.group(1) or ""

            if open_:
                code_fences.append((i, lang))
                line_breaks.extend([i, i + 1])
            else:
                code_fences.append(i)

    # Rewrite fenced code blocks
    open_ = -1
    for fence in code_fences:
        if isinstance(fence, tuple):
            open_ = fence[0] + 1
            lines[fence[0]] = f".. code-block:: {fence[1]}"
        else:
            # Indent content
            for j in range(open_, fence):
                lines[j] = f"   {lines[j]}"

            lines[fence] = ""

    # Insert extra line breaks
    for offset, line in enumerate(line_breaks):
        lines.insert(line + offset, "")


class CapabilitiesDomain(Domain):
    name = "capabilities"

    directives = {
        "bool-table": BoolTable,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.clients = _load_clients()
        self.analyzer = ModuleAnalyzer.for_module("lsprotocol.types")
        self.analyzer.analyze()

    def get_capability_documentation(self, field_name: str) -> List[str]:
        """Return the documentation associated with the given capability."""
        type_ = types.ClientCapabilities
        parent = type_.__name__

        *parents, field = field_name.split(".")
        for p in parents:
            attr = attrs.fields_dict(type_)[p]

            type_ = attr.type
            if len(args := typing.get_args(type_)) > 0:
                type_ = args[0]

            parent = type_.__name__

        lines = self.analyzer.attr_docs.get((parent, field), [])
        process_docstring(lines)

        return lines


def setup(app: Sphinx):
    app.add_domain(CapabilitiesDomain)
