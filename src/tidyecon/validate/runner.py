"""
validate/runner.py
==================
Runs tidy() against hardcoded R/Stata benchmarks and reports
numerical equivalence.

CLI:  tidyecon-validate
      python -m tidyecon.validate.runner
"""
from __future__ import annotations

import math
import sys
import textwrap
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from .._adapters import tidy as _tidy
from .fixtures import ALL_FIXTURES, CoefFixture, ModelFixture


@dataclass
class CheckResult:
    fixture_name: str
    term: str
    field: str
    expected: float
    actual: float
    tolerance: float
    passed: bool

    @property
    def delta(self) -> float:
        return abs(self.actual - self.expected)


@dataclass
class FixtureResult:
    fixture: ModelFixture
    checks: list[CheckResult]
    build_error: str | None = None

    @property
    def passed(self) -> bool:
        return self.build_error is None and all(c.passed for c in self.checks)

    @property
    def n_fail(self) -> int:
        return sum(1 for c in self.checks if not c.passed)


# ── Core runner ───────────────────────────────────────────────────────────────

def run_fixture(fixture: ModelFixture) -> FixtureResult:
    """Build the model from fixture.model_factory and compare tidy() output."""
    # Build model
    ns: dict[str, Any] = {}
    try:
        exec(fixture.model_factory, ns)
        model = ns["model"]
    except Exception as e:
        return FixtureResult(fixture=fixture, checks=[], build_error=str(e))

    # Extract tidy
    try:
        df = _tidy(model)
    except Exception as e:
        return FixtureResult(fixture=fixture, checks=[], build_error=f"tidy() failed: {e}")

    checks: list[CheckResult] = []
    for coef_fix in fixture.coefs:
        term_rows = df[df["term"] == coef_fix.term]
        if term_rows.empty:
            # Term not found — fail all checks for this term
            for fld in ("estimate", "std_error", "statistic"):
                checks.append(CheckResult(
                    fixture_name=fixture.name,
                    term=coef_fix.term,
                    field=fld,
                    expected=getattr(coef_fix, fld),
                    actual=float("nan"),
                    tolerance=fixture.tol_coef,
                    passed=False,
                ))
            continue

        row = term_rows.iloc[0]

        field_tol = {
            "estimate":  fixture.tol_coef,
            "std_error": fixture.tol_se,
            "statistic": fixture.tol_coef * 10,  # t-stats accumulate error
        }
        field_map = {
            "estimate":  float(row["estimate"]),
            "std_error": float(row["std_error"]),
            "statistic": float(row["statistic"]),
        }
        expected_map = {
            "estimate":  coef_fix.estimate,
            "std_error": coef_fix.std_error,
            "statistic": coef_fix.statistic,
        }

        for fld, actual in field_map.items():
            expected = expected_map[fld]
            tol      = field_tol[fld]
            passed   = (
                math.isnan(expected) and math.isnan(actual)
            ) or abs(actual - expected) <= tol

            checks.append(CheckResult(
                fixture_name=fixture.name,
                term=coef_fix.term,
                field=fld,
                expected=expected,
                actual=actual,
                tolerance=tol,
                passed=passed,
            ))

    return FixtureResult(fixture=fixture, checks=checks)


def run_all(fixtures=ALL_FIXTURES) -> list[FixtureResult]:
    return [run_fixture(f) for f in fixtures]


# ── Reporter ──────────────────────────────────────────────────────────────────

def report(results: list[FixtureResult], verbose: bool = True) -> int:
    """Print a human-readable report. Returns exit code (0=pass, 1=fail)."""
    total_checks = 0
    failed_checks = 0
    print("\n" + "═" * 72)
    print("  tidyecon  numerical validation against R benchmarks")
    print("═" * 72)

    for res in results:
        icon = "✓" if res.passed else "✗"
        print(f"\n  [{icon}] {res.fixture.name}")
        print(f"       {res.fixture.description}")
        print(f"       source: {res.fixture.source}")

        if res.build_error:
            print(f"       ERROR building model: {res.build_error}")
            failed_checks += 1
            total_checks  += 1
            continue

        for chk in res.checks:
            total_checks += 1
            status = "PASS" if chk.passed else "FAIL"
            if not chk.passed or verbose:
                flag = "" if chk.passed else "  ← FAIL"
                print(
                    f"       {status}  {chk.term:20s} {chk.field:12s} "
                    f"expected={chk.expected:+.6g}  "
                    f"actual={chk.actual:+.6g}  "
                    f"Δ={chk.delta:.2e}{flag}"
                )
            if not chk.passed:
                failed_checks += 1

    print("\n" + "─" * 72)
    print(f"  {total_checks - failed_checks}/{total_checks} checks passed")
    if failed_checks:
        print(f"  {failed_checks} check(s) FAILED")
    print("─" * 72 + "\n")
    return 1 if failed_checks else 0


# ── CLI entry point ────────────────────────────────────────────────────────────

def cli() -> None:
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    results  = run_all()
    code     = report(results, verbose=verbose)
    sys.exit(code)


if __name__ == "__main__":
    cli()
