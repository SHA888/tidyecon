"""
_protocol.py
============
Defines the canonical column schema for tidy() and glance() outputs.
All adapters MUST conform to these schemas.  Any downstream renderer
or summary builder can rely on these column names unconditionally.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

# ── Coefficient-level schema ─────────────────────────────────────────────────
TIDY_COLS: list[str] = [
    "term",  # str  – variable name
    "estimate",  # float – point estimate
    "std_error",  # float – standard error
    "statistic",  # float – t / z stat
    "p_value",  # float – two-sided p-value
    "conf_low",  # float – lower confidence bound
    "conf_high",  # float – upper confidence bound
]

# ── Model-level schema ────────────────────────────────────────────────────────
GLANCE_COLS: list[str] = [
    "nobs",  # int   – number of observations
    "r_squared",  # float – R²  (NaN if not applicable)
    "adj_r_squared",  # float – adjusted R²
    "rmse",  # float – root mean squared error
    "f_statistic",  # float – F-statistic (NaN if not applicable)
    "p_value_f",  # float – p-value of F-test
    "df_model",  # float – model degrees of freedom
    "df_residual",  # float – residual degrees of freedom
    "estimator",  # str   – human-readable estimator name
    "fixed_effects",  # str   – FE spec string, e.g. "firm+year"  (empty if none)
    "vcov_type",  # str   – variance estimator, e.g. "CRV1", "HC3"
]


def _empty_tidy() -> pd.DataFrame:
    return pd.DataFrame(columns=TIDY_COLS)


def _empty_glance() -> pd.DataFrame:
    return pd.DataFrame(columns=GLANCE_COLS)


def _validate_tidy(df: pd.DataFrame) -> pd.DataFrame:
    """Enforce schema: add missing columns as NaN, drop extras, reorder."""
    for col in TIDY_COLS:
        if col not in df.columns:
            df[col] = np.nan
    result = df[TIDY_COLS].reset_index(drop=True)
    # Ensure we always return a DataFrame, even if result is a Series
    return result if isinstance(result, pd.DataFrame) else result.to_frame()


def _validate_glance(df: pd.DataFrame) -> pd.DataFrame:
    for col in GLANCE_COLS:
        if col not in df.columns:
            df[col] = (
                np.nan
                if col != "fixed_effects" and col != "vcov_type" and col != "estimator"
                else ""
            )
    result = df[GLANCE_COLS].reset_index(drop=True)
    # Ensure we always return a DataFrame, even if result is a Series
    return result if isinstance(result, pd.DataFrame) else result.to_frame()


# ── Internal table row (used by renderers) ────────────────────────────────────
@dataclass
class TableRow:
    label: str
    values: list[str]
    is_stat: bool = False  # SE / t-stat row — rendered smaller / italic
    is_separator: bool = False  # horizontal rule
    is_gof: bool = False  # goodness-of-fit section


@dataclass
class SummaryTable:
    """Intermediate representation consumed by all renderers."""

    col_labels: list[str]  # e.g. ["(1)", "(2)", "(3)"]
    rows: list[TableRow]
    title: str | None = None
    notes: list[str] = field(default_factory=list)
    stars_legend: str = "* p<0.1  ** p<0.05  *** p<0.01"


# ── Star thresholds ───────────────────────────────────────────────────────────
DEFAULT_STARS: dict[str, float] = {"***": 0.01, "**": 0.05, "*": 0.10}


def _stars(p: float, thresholds: dict[str, float] = DEFAULT_STARS) -> str:
    if np.isnan(p):
        return ""
    for symbol, cutoff in sorted(thresholds.items(), key=lambda x: x[1]):
        if p < cutoff:
            return symbol
    return ""
