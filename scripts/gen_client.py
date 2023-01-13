"""Script to automatically generate a lanaguge client from `lsprotocol` type definitons
"""
import argparse
import inspect
import pathlib
import re
import sys
import textwrap
from datetime import datetime
from typing import List
from typing import Optional
from typing import Tuple
from typing import Type
from typing import Union

from lsprotocol._hooks import _resolve_forward_references
from lsprotocol.types import METHOD_TO_TYPES
from lsprotocol.types import message_direction

cli = argparse.ArgumentParser(
    description="generate language client from lsprotocol types."
)
cli.add_argument("-o", "--output", default=None)


def write_imports(imports: List[Union[str, Tuple[str, str]]]) -> str:
    lines = []

    for import_ in sorted(imports, key=lambda i: (i[0], i[1])):
        if isinstance(import_, tuple):
            mod, name = import_
            lines.append(f"from {mod} import {name}")
            continue

        lines.append(f"import {import_}")

    return "\n".join(lines)


def to_snake_case(string: str) -> str:
    return "".join(f"_{c.lower()}" if c.isupper() else c for c in string)


def write_notification(
    method: str,
    request: Type,
    params: Optional[Type],
    imports: List[Union[str, Tuple[str, str]]],
) -> str:

    python_name = to_snake_case(method).replace("/", "_").replace("$_", "")

    if params is None:
        param_name = "None"
    else:
        param_mod, param_name = params.__module__, params.__name__
        imports.append((param_mod, param_name))

    return "\n".join(
        [
            f"def notify_{python_name}(self, params: {param_name}) -> None:",
            f'    """Send a ``{method}`` notification.',
            "",
            textwrap.indent(inspect.getdoc(request) or "", "    "),
            '    """',
            f'    self.lsp.notify("{method}", params)',
            "",
        ]
    )


def write_method(
    method: str,
    request: Type,
    params: Optional[Type],
    response: Type,
    imports: List[Union[str, Tuple[str, str]]],
) -> str:

    python_name = to_snake_case(method).replace("/", "_").replace("$_", "")

    if params is None:
        param_name = "None"
    else:
        param_mod, param_name = params.__module__, params.__name__
        imports.append((param_mod, param_name))

    # Find the response type.
    result_field = [f for f in response.__attrs_attrs__ if f.name == "result"][0]
    result = re.sub(r"<class '([\w.]+)'>", r"\1", str(result_field.type))
    result = re.sub(r"ForwardRef\('([\w.]+)'\)", r"lsprotocol.types.\1", result)
    result = result.replace("NoneType", "None")

    return "\n".join(
        [
            f"async def {python_name}_request(self, params: {param_name}) -> {result}:",
            f'    """Make a ``{method}`` request.',
            "",
            textwrap.indent(inspect.getdoc(request) or "", "    "),
            '    """',
            f'    return await self.lsp.send_request_async("{method}", params)',
            "",
        ]
    )


def generate_client() -> str:

    methods = []
    imports = [
        "typing",
        "lsprotocol.types",
        ("pygls.server", "Server"),
    ]

    for method_name, types in METHOD_TO_TYPES.items():

        if message_direction(method_name) == "serverToClient":
            continue

        request, response, params, _ = types

        if response is None:
            method = write_notification(method_name, request, params, imports)
        else:
            method = write_method(method_name, request, params, response, imports)

        methods.append(textwrap.indent(method, "    "))

    code = [
        "# GENERATED FROM scripts/gen-client.py -- DO NOT EDIT",
        f"# Last Modified: {datetime.now()}",
        "# flake8: noqa",
        write_imports(imports),
        "",
        "",
        "class Client(Server):",
        '    """Used to drive the language server under test."""',
        "",
        *methods,
    ]
    return "\n".join(code)


def main():
    args = cli.parse_args()

    # Make sure all the type annotations in lsprotocol are resolved correctly.
    _resolve_forward_references()
    client = generate_client()

    if args.output is None:
        sys.stdout.write(client)
    else:
        output = pathlib.Path(args.output)
        output.write_text(client)


if __name__ == "__main__":
    main()
