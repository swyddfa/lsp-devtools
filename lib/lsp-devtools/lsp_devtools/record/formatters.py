from __future__ import annotations

import json
import typing
from functools import partial

import lsprotocol.types

if typing.TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any


def format_json(obj: dict, *, indent: str | int | None = 2) -> str:
    if isinstance(obj, str):
        return obj

    return json.dumps(obj, indent=indent, default=unwrap_value_formatter)


def unwrap_value_formatter(o):
    """Fallback function for json.dumps that unwraps ValueFormatter instances"""

    if isinstance(o, ValueFormatter):
        return o.value

    raise TypeError(f"Object not JSON serializable: {o.__class__.__name__}")


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


class ValueFormatter:
    """Constains a value to be formatted according to our own format syntax."""

    def __init__(self, value: Any):
        self.value: Any = value

    def __repr__(self):
        return repr(self.value)

    def __getattr__(self, key: str):
        if isinstance(self.value, dict):
            try:
                return ValueFormatter(self.value[key])
            except KeyError as exc:
                raise AttributeError(key) from exc

        if isinstance(self.value, list):
            values = [getattr(ValueFormatter(v), key) for v in self.value]
            return ValueFormatter(value=values)

        raise AttributeError(key)

    def __getitem__(self, key):
        if isinstance(self.value, dict):
            return ValueFormatter(value=self.value[key])

        if isinstance(self.value, list):
            # For some reason, when used in a format string, 'key' is a string rather
            # than an actual slice...
            if isinstance(key, str):
                idx = parse_slice(key)

            else:
                idx = key

            if isinstance(result := self.value[idx], list):
                return ValueFormatter(result)
            else:
                return ValueFormatter(result)

    def __format__(self, spec: str) -> str:
        formatter = get_formatter(spec or "json")
        return formatter(self.value)


def parse_slice(value: str) -> int | slice:
    value = value.strip()
    if ":" not in value:
        return int(value)

    if len(parts := value.split(":")) > 3:
        raise ValueError(f"Invalid slice notation: {value!r}")

    args: list[int | None] = []
    for part in parts:
        part = part.strip()
        args.append(int(part) if part else None)

    while len(args) < 3:
        args.append(None)

    return slice(*args)
