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


@pytest.mark.parametrize("name", ["getting-started", "window-log-message"])
def test_documentation_examples(pytester: pytest.Pytester, name: str):
    """Ensure that the examples included in the documentation work as expected."""

    setup_test(pytester, name)

    results = pytester.runpytest()
    results.assert_outcomes(passed=1)


def test_getting_started_fail(pytester: pytest.Pytester):
    """Ensure that the initial getting started example fails as expected."""

    setup_test(pytester, "getting-started-fail")

    results = pytester.runpytest()
    results.assert_outcomes(errors=1)

    if sys.version_info.minor < 9:
        message = "E*CancelledError"
    else:
        message = "E*asyncio.exceptions.CancelledError: RuntimeError: Server exited with return code: 0"  # noqa: E501

    results.stdout.fnmatch_lines(message)


def test_window_log_message_fail(pytester: pytest.Pytester):
    """Ensure that the initial getting started example fails as expected."""

    setup_test(pytester, "window-log-message-fail")

    results = pytester.runpytest()
    results.assert_outcomes(failed=1)

    results.stdout.fnmatch_lines("* Captured window/logMessages call")
    results.stdout.fnmatch_lines("  LOG: Suggesting item 0")
    results.stdout.fnmatch_lines("  LOG: Suggesting item 1")
    results.stdout.fnmatch_lines("  LOG: Suggesting item 2")
    results.stdout.fnmatch_lines("  LOG: Suggesting item 3")
    results.stdout.fnmatch_lines("  LOG: Suggesting item 4")
    results.stdout.fnmatch_lines("  LOG: Suggesting item 5")
    results.stdout.fnmatch_lines("  LOG: Suggesting item 6")
    results.stdout.fnmatch_lines("  LOG: Suggesting item 7")
    results.stdout.fnmatch_lines("  LOG: Suggesting item 8")
    results.stdout.fnmatch_lines("  LOG: Suggesting item 9")
