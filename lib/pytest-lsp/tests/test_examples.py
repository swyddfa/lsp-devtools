import pathlib
import sys

import pytest

EXAMPLES = pathlib.Path(__file__).parent / "examples"


def setup_test(pytester: pytest.Pytester, example_name: str):
    pytester.makeini(
        """\
[pytest]
asyncio_mode = auto
"""
    )

    for src in (EXAMPLES / example_name).glob("*.py"):
        if not src.is_file():
            continue

        dest = pytester.path / src.name.replace("t_", "test_")
        dest.write_text(src.read_text())


def test_getting_started(pytester: pytest.Pytester):
    """Ensure that the initial getting started exampl eworks as expected."""

    setup_test(pytester, "getting-started")

    results = pytester.runpytest("-vv")
    results.assert_outcomes(passed=1)


def test_getting_started_fail(pytester: pytest.Pytester):
    """Ensure that the initial getting started example fails as expected."""

    setup_test(pytester, "getting-started-fail")

    results = pytester.runpytest("-vv")
    results.assert_outcomes(errors=1)

    if sys.version_info.minor < 9:
        message = "E*CancelledError"
    else:
        message = "E*asyncio.exceptions.CancelledError: RuntimeError: Server exited with return code: 0"  # noqa: E501

    results.stdout.fnmatch_lines(message)
