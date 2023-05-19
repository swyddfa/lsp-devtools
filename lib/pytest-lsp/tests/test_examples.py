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


@pytest.mark.parametrize(
    "name, expected",
    [
        ("diagnostics", dict(passed=1)),
        ("getting-started", dict(passed=1)),
        ("parameterised-clients", dict(passed=2)),
        ("window-log-message", dict(passed=1)),
        ("window-show-document", dict(passed=1)),
        ("window-show-message", dict(passed=1)),
    ],
)
def test_documentation_examples(pytester: pytest.Pytester, name: str, expected: dict):
    """Ensure that the examples included in the documentation work as expected."""

    setup_test(pytester, name)

    results = pytester.runpytest()
    results.assert_outcomes(**expected)


def test_client_capabilities(pytester: pytest.Pytester):
    """Ensure that the client capabilities example warns as expected."""

    setup_test(pytester, "client-capabilities")

    results = pytester.runpytest(
        "-W", "ignore::DeprecationWarning:pytest_asyncio.plugin"
    )
    results.assert_outcomes(passed=1, warnings=1)

    message = "*LspSpecificationWarning: Client does not support snippets."
    results.stdout.fnmatch_lines(message)


def test_client_capabilities_error(pytester: pytest.Pytester):
    """Ensure that the client capabilities warnings can be upgraded to errors."""

    setup_test(pytester, "client-capabilities")

    results = pytester.runpytest("-W", "error::pytest_lsp.LspSpecificationWarning")
    results.assert_outcomes(failed=1)

    message = (
        "E*pytest_lsp.checks.LspSpecificationWarning: Client does not support snippets."
    )
    results.stdout.fnmatch_lines(message)


def test_client_capabilities_ignore(pytester: pytest.Pytester):
    """Ensure that the client capabilities warnings can be ignored."""

    setup_test(pytester, "client-capabilities")

    results = pytester.runpytest(
        "-W",
        "ignore::pytest_lsp.LspSpecificationWarning",
        "-W",
        "ignore::DeprecationWarning:pytest_asyncio.plugin",
    )
    results.assert_outcomes(passed=1, warnings=0)


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

    results.stdout.fnmatch_lines("-* Captured window/logMessages call -*")
    results.stdout.fnmatch_lines(" *LOG: Suggesting item 0")
    results.stdout.fnmatch_lines(" *LOG: Suggesting item 1")
    results.stdout.fnmatch_lines(" *LOG: Suggesting item 2")
    results.stdout.fnmatch_lines(" *LOG: Suggesting item 3")
    results.stdout.fnmatch_lines(" *LOG: Suggesting item 4")
    results.stdout.fnmatch_lines(" *LOG: Suggesting item 5")
    results.stdout.fnmatch_lines(" *LOG: Suggesting item 6")
    results.stdout.fnmatch_lines(" *LOG: Suggesting item 7")
    results.stdout.fnmatch_lines(" *LOG: Suggesting item 8")
    results.stdout.fnmatch_lines(" *LOG: Suggesting item 9")
