import json
import pathlib
import sys

from lsprotocol import types
from lsprotocol.converters import get_converter


def check(filepath: pathlib.Path, converter):
    obj = json.loads(filepath.read_text())

    try:
        converter.structure(obj, types.InitializeParams)
    except Exception as e:
        print(f"{filepath.name}: {e}")
        return 1

    filepath.write_text(json.dumps(obj, indent=2))
    return 0


def main(files: list[str]):
    converter = get_converter()

    total = 0
    for filename in files:
        total += check(pathlib.Path(filename), converter)

    return total


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
