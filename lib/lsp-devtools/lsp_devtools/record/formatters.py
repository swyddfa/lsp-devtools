from __future__ import annotations

import json
import re
import typing
from functools import cache
from functools import partial

import lsprotocol.types

if typing.TYPE_CHECKING:
    from typing import Any
    from typing import Callable


def format_json(obj: dict, *, indent: str | int | None = 2) -> str:
    if isinstance(obj, str):
        return obj

    return json.dumps(obj, indent=indent)


def format_position(position: dict) -> str:
    return f"{position['line']}:{position['character']}"


def format_range(range_: dict) -> str:
    return f"{format_position(range_['start'])}-{format_position(range_['end'])}"


FORMATTERS: dict[str, Callable[[Any], str]] = {
    "position": format_position,
    "range": format_range,
    "json": format_json,
    "json-compact": partial(format_json, indent=None),
}


def get_formatter(fmt: str) -> Callable[[Any], str]:
    """Return the formatter with the given name."""

    formatter = FORMATTERS.get(fmt.lower(), None)
    if formatter is not None:
        return formatter

    # Is the formatter is an enum?
    enum = getattr(lsprotocol.types, fmt, None)
    if enum is not None:

        def fn(v: int) -> str:
            return enum(v).name  # type: ignore

        return fn

    raise TypeError(f"Unknown format: '{fmt}'")


class Value:
    """Represents a value to be inserted into a string."""

    LIST_FIELD = re.compile(r"(.*)\[(.*)?\]")

    def __init__(self, accessor: str, formatter: Callable[[Any], str]):
        self.accessor = accessor
        self.formatter = formatter

    def __repr__(self):
        return f'Value(accessor="{self.accessor}", formatter={self.formatter})'

    def format(self, message: dict, accessor: str | None = None) -> str:
        """Convert a message to a string according to the current accessor and
        formatter."""

        idx = 0
        obj = message
        accessor = self.accessor if accessor is None else accessor

        for field in accessor.split("."):
            if not field:
                continue

            # TODO: Once we have a better idea on what we want the list syntax to be,
            # most of this should be move into the format string parsing code, so that
            # it only runs once.
            idx += len(field)
            match = self.LIST_FIELD.fullmatch(field)
            if match:
                obj = obj[match.group(1)]
                remainder = accessor[idx + 1 :]
                sep, index = get_separator_index(match.group(2))

                if isinstance(index, int):
                    obj = obj[index]
                    continue

                if isinstance(index, slice):
                    obj = obj[index]

                return sep.join([self.format(o, remainder) for o in obj])

            obj = obj[field]

        return self.formatter(obj)


@cache
def get_separator_index(separator: str) -> tuple[str, int | slice | None]:
    if not separator:
        return "\n", None

    if "#" in separator:
        idx, sep = separator.split("#")
        return get_separator(sep), get_index(idx)

    # Try parsing as an index
    index = get_index(separator)
    if index is not None:
        return "\n", index

    # It must be just a separator then.
    return get_separator(separator), None


def get_separator(sep: str) -> str:
    if not sep:
        return "\n"

    return sep.replace("\\n", "\n").replace("\\t", "\t")


def get_index(idx: str) -> int | slice | None:
    try:
        return int(idx)
    except ValueError:
        pass

    if ":" in idx:
        parts = idx.split(":")

        try:
            return slice(*[int(p) for p in parts])
        except ValueError:
            pass

    return None


class FormatString:
    """Implements the format string syntax.

    [{.params.type:MessageType}]: {.params.message} and something else
    """

    VARIABLE = re.compile(r"{\.([^}]+)}")

    def __init__(self, pattern: str):
        self.pattern = pattern  # .replace("\\n", "\n").replace("\\t", "\t")
        self._parse()

    def _parse(self):
        idx = 0
        parts: list[str | Value] = []

        for match in self.VARIABLE.finditer(self.pattern):
            start, end = match.span()
            parts.append(self.pattern[idx:start])

            variable = match.group(1)
            if "|" in variable:
                accessor, fmt = variable.split("|")
                formatter = get_formatter(fmt)
            else:
                accessor = variable
                formatter = format_json

            parts.append(Value(accessor=accessor, formatter=formatter))
            idx = end

        parts.append(self.pattern[idx:])
        self.parts = parts

    def format(self, message: dict) -> str:
        return "".join([p.format(message) for p in self.parts])
