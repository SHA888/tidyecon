"""
tests/test_validate.py
======================
Runs the built-in validation suite and asserts all fixtures pass.
This is the automated equivalent of "does our tidy() match R?"
"""

from tidyecon.validate.runner import report, run_all


def test_all_fixtures_pass(capsys):
    results = run_all()
    exit_code = report(results, verbose=True)
    assert exit_code == 0, (
        "One or more numerical validation fixtures failed. "
        "Run `tidyecon-validate -v` for details."
    )
