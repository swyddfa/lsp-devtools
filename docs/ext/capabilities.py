import enum
import importlib.resources as resources
import json
import operator
import pathlib
import re
import typing
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import attrs
from docutils import nodes
from docutils.parsers.rst import directives
from docutils.statemachine import StringList
from lsprotocol import types
from lsprotocol.converters import get_converter
from packaging.version import parse as parse_version
from pygls.capabilities import get_capability
from sphinx import addnodes
from sphinx.application import Sphinx
from sphinx.directives import ObjectDescription
from sphinx.domains import Domain
from sphinx.pycode import ModuleAnalyzer
from sphinx.util.docutils import SphinxDirective


class CapabilityTable(ObjectDescription[str]):
    """Base directive for generating tables describing support for LSP capabilities."""

    def handle_signature(self, sig: str, signode: addnodes.desc_signature) -> str:
        """Render the name of the capability."""
        try:
            name = to_camel_case(sig)
            parts = name.split(".")
            parent_name = ".".join(parts[:-1]) + "."

            domain = self.env.domains[self.domain]
            documentation, lsp_version = domain.get_capability_documentation(sig)

            # Save the documentation from the spec until we can insert it into the page
            self.env.temp_data["extra-capability-documentation"] = documentation

            if lsp_version:
                signode += addnodes.desc_annotation(
                    lsp_version,
                    "",
                    addnodes.desc_sig_literal_string("", f"since v{lsp_version}"),
                    addnodes.desc_sig_space(),
                )

            signode["ids"].append(name)
            signode["python-name"] = sig
            signode["spec-name"] = name
            signode += addnodes.desc_addname(parent_name, parent_name)
            signode += addnodes.desc_name("", parts[-1])

            return name
        except Exception as exc:
            breakpoint()
            return ...

    def _object_hierarchy_parts(
        self, signode: addnodes.desc_signature
    ) -> Tuple[str, ...]:
        """Return the full hierarchy of the capability, used for toctree generation."""
        name = signode["spec-name"]
        return tuple(name.split(".")[:-1])

    def _toc_entry_name(self, signode: addnodes.desc_signature) -> str:
        """Return the name of capability, used for toctree generation."""
        name = signode["spec-name"]
        return name.split(".")[-1]

    def render_table(self, contentnode: addnodes.desc_content):
        """Render the table to insert into the page."""
        return []

    def transform_content(self, contentnode: addnodes.desc_content):
        """Insert documentation about the capability."""

        contentnode += self.render_table(contentnode)

        documentation = self.env.temp_data["extra-capability-documentation"]
        if len(documentation) > 0:
            self.state.nested_parse(StringList(documentation), 0, contentnode)


class BoolCapabilityTable(CapabilityTable):
    """Given a boolean capability, indicate the support across known clients and
    versions"""

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

        for name, version in sorted(clients.items(), key=operator.itemgetter(0)):
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

    def render_table(self, contentnode: addnodes.desc_content):
        capability = contentnode.parent[0]["python-name"]

        header, colspecs = self.build_header()
        body = self.build_body(capability)

        table = nodes.table("", nodes.tgroup("", *colspecs, header, body))

        return [table]


class ValueSetCapabilityTable(CapabilityTable):
    """Given a capability that enumerates a set of values, indicate their support across
    known clients and versions."""

    option_spec = {
        "value-set": directives.unchanged,
        **CapabilityTable.option_spec,
    }

    def get_known_values(self, capability: str):
        values = set()
        domain = self.env.domains["capabilities"]

        for capabilities in domain.clients.values():
            client_values = get_capability(capabilities, capability, [])
            if not isinstance(client_values, list):
                client_values = [client_values]

            for value in client_values:
                if isinstance(value, enum.Enum):
                    if isinstance(value, int):
                        values.add(value.name)
                    else:
                        values.add(value.value)
                else:
                    values.add(value)

        return sorted(list(values))

    def get_values(self, capability: str):
        if (value_set := self.options.get("value-set", None)) is None:
            # No pre-defined list, return a list of all values we see in our client
            # capabilities
            return self.get_known_values(capability)

        # TODO: Handle int enums...
        value_set_type = getattr(types, value_set)
        if issubclass(value_set_type, int):
            return sorted([v.name for v in list(value_set_type)])
        else:
            return sorted([v.value for v in list(value_set_type)])

    def build_header(self, capability: str):
        values = self.get_values(capability)

        colspecs = [nodes.colspec("", colwidth="4")] + [
            nodes.colspec("", colwidth="1") for _ in range(len(values))
        ]
        header = nodes.thead(
            "",
            nodes.row(
                "",
                nodes.entry("", nodes.Text("Client")),
                *[nodes.entry("", nodes.literal(value, value)) for value in values],
            ),
        )

        return header, colspecs

    def get_client_support_for(self, capability: str):
        domain = self.env.domains["capabilities"]
        values = self.get_values(capability)

        clients = {}
        for (name, version), capabilities in domain.clients.items():
            if name not in clients:
                clients[name] = {v: None for v in values}

            supported_values = get_capability(capabilities, capability, None)
            if supported_values is None:
                continue

            if not isinstance(supported_values, list):
                supported_values = [supported_values]

            supported_values = set(supported_values)
            for value in clients[name]:
                if value not in supported_values:
                    continue

                if (existing := clients[name][value]) is None:
                    clients[name][value] = version
                else:
                    clients[name][value] = min(existing, version, key=parse_version)

        client_support = {
            name: [(v, value[v]) for v in values] for name, value in clients.items()
        }

        return client_support

    def build_body(self, capability: str):
        rows = []
        clients = self.get_client_support_for(capability)

        for name, support in sorted(clients.items(), key=operator.itemgetter(0)):
            cells = []

            for _, supported_version in support:
                cells.append(
                    nodes.entry(
                        "",
                        nodes.Text(supported_version or " - "),
                        classes=["centered"],
                    ),
                )

            rows.append(nodes.row("", nodes.entry("", nodes.Text(name)), *cells))

        return nodes.tbody("", *rows)

    def render_table(self, contentnode: addnodes.desc_content):
        capability = contentnode.parent[0]["python-name"]

        header, colspecs = self.build_header(capability)
        body = self.build_body(capability)

        table = nodes.table("", nodes.tgroup("", *colspecs, header, body))
        return table


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


def process_docstring(lines: List[str]) -> Optional[str]:
    """Fixup LSP docstrings so that they work with reStructuredText syntax

    This modifies the give ``lines`` in-place to:

    - Replace ``{@link <item>}`` with ``:class:`~lsprotocol.types.<item>` ``

    - Replace markdown hyperlink with reStructuredText equivalent

    - Replace inline markdown code (single "`") with reStructuredText inline code
      (double "`")

    - Insert the required newline before a bulleted list

    - Replace code fences with code blocks

    - Fixe indentation

    Returns
    -------
    str
       If ``@since <version>`` was found, the version string will be returned.
    """

    line_breaks = []
    code_fences = []
    lsp_version: Optional[str] = None

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
            lsp_version = match.group(1)

            # Remove the @since declaration from the given set of lines.
            lines[i] = "".join([line[:start], line[end:]])

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

    return lsp_version


class CapabilitiesDomain(Domain):
    name = "capabilities"

    directives = {
        "bool-table": BoolCapabilityTable,
        "values-table": ValueSetCapabilityTable,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.clients = _load_clients()
        self.analyzer = ModuleAnalyzer.for_module("lsprotocol.types")
        self.analyzer.analyze()

    def get_capability_documentation(
        self, field_name: str
    ) -> Tuple[List[str], Optional[str]]:
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
        lsp_version = process_docstring(lines)

        return lines, lsp_version


def setup(app: Sphinx):
    app.add_domain(CapabilitiesDomain)
