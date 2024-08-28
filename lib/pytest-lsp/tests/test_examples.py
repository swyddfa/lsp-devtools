import pathlib

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
        pytest.param("diagnostics", dict(passed=1), id="diagnostics"),
        pytest.param("getting-started", dict(passed=1), id="getting-started"),
        pytest.param("fixture-passthrough", dict(passed=1), id="fixture-passthrough"),
        pytest.param("fixture-scope", dict(passed=2), id="fixture-scope"),
        pytest.param(
            "parameterised-clients", dict(passed=2), id="parameterised-clients"
        ),
        pytest.param("window-log-message", dict(passed=1), id="window-log-message"),
        pytest.param(
            "window-create-progress",
            dict(passed=3),
            id="window-create-progress",
        ),
        pytest.param("window-show-document", dict(passed=1), id="window-show-document"),
        pytest.param("window-show-message", dict(passed=1), id="window-show-message"),
        pytest.param(
            "workspace-configuration",
            dict(passed=1, warnings=1),
            id="workspace-configuration",
        ),
    ],
)
def test_examples(pytester: pytest.Pytester, name: str, expected: dict):
    """Ensure that the examples included in the documentation work as expected."""

    setup_test(pytester, name)

    results = pytester.runpytest()
    results.assert_outcomes(**expected)


def test_client_capabilities(pytester: pytest.Pytester):
    """Ensure that the client capabilities example warns as expected."""

    setup_test(pytester, "client-capabilities")

    results = pytester.runpytest()
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
    )
    results.assert_outcomes(passed=1, warnings=0)


def test_getting_started_fail(pytester: pytest.Pytester):
    """Ensure that the initial getting started example fails as expected."""

    setup_test(pytester, "getting-started-fail")

    results = pytester.runpytest()
    results.assert_outcomes(errors=1)

    message = r"E\s+RuntimeError: Server process \d+ exited with code: 0"
    results.stdout.re_match_lines(message)


def test_generic_rpc(pytester: pytest.Pytester):
    """Ensure that the generic rpc example works as expected"""

    setup_test(pytester, "generic-rpc")

    results = pytester.runpytest("--log-cli-level", "info")
    results.assert_outcomes(passed=1, failed=1)

    results.stdout.fnmatch_lines(" *LOG: a=1")
    results.stdout.fnmatch_lines(" *LOG: b=2")


def test_server_stderr_fail(pytester: pytest.Pytester):
    """Ensure that the server's stderr stream is presented on failure."""

    setup_test(pytester, "server-stderr")

    results = pytester.runpytest()
    results.assert_outcomes(failed=1)

    results.stdout.fnmatch_lines("-* Captured stderr call -*")
    results.stdout.fnmatch_lines("Suggesting item 0")
    results.stdout.fnmatch_lines("Suggesting item 1")
    results.stdout.fnmatch_lines("Suggesting item 2")
    results.stdout.fnmatch_lines("Suggesting item 3")
    results.stdout.fnmatch_lines("Suggesting item 4")
    results.stdout.fnmatch_lines("Suggesting item 5")
    results.stdout.fnmatch_lines("Suggesting item 6")
    results.stdout.fnmatch_lines("Suggesting item 7")
    results.stdout.fnmatch_lines("Suggesting item 8")
    results.stdout.fnmatch_lines("Suggesting item 9")


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
