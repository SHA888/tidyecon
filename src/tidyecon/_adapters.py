"""
_adapters.py
============
Dispatch-based tidy() and glance() implementations.

Design principle: zero modifications to upstream model objects.
We use isinstance() dispatch keyed on lazy imports so that missing
optional dependencies raise a clear error only when actually needed.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from ._protocol import (
    _validate_glance,
    _validate_tidy,
)

# ── Public API ────────────────────────────────────────────────────────────────


def tidy(model: Any, conf_level: float = 0.95) -> pd.DataFrame:
    """
    Extract coefficient-level statistics from a fitted model.

    Parameters
    ----------
    model : fitted model object (statsmodels / pyfixest / linearmodels)
    conf_level : confidence level for intervals (default 0.95)

    Returns
    -------
    pd.DataFrame with columns: term, estimate, std_error, statistic,
                                p_value, conf_low, conf_high
    """
    adapter = _dispatch_tidy(model)
    df = adapter(model, conf_level=conf_level)
    return _validate_tidy(df)


def glance(model: Any) -> pd.DataFrame:
    """
    Extract model-level summary statistics.

    Returns
    -------
    Single-row pd.DataFrame with columns defined in GLANCE_COLS.
    """
    adapter = _dispatch_glance(model)
    df = adapter(model)
    return _validate_glance(df)


# ── Dispatch ──────────────────────────────────────────────────────────────────


def _dispatch_tidy(model: Any):
    if _is_statsmodels(model):
        return _tidy_statsmodels
    if _is_pyfixest(model):
        return _tidy_pyfixest
    if _is_linearmodels(model):
        return _tidy_linearmodels
    raise TypeError(
        f"tidyecon: no tidy() adapter for {type(model).__qualname__}.\n"
        f"Supported: statsmodels results, pyfixest Feols/Fepois, "
        f"linearmodels panel/IV results."
    )


def _dispatch_glance(model: Any):
    if _is_statsmodels(model):
        return _glance_statsmodels
    if _is_pyfixest(model):
        return _glance_pyfixest
    if _is_linearmodels(model):
        return _glance_linearmodels
    raise TypeError(f"tidyecon: no glance() adapter for {type(model).__qualname__}.")


# ── Type guards (lazy imports) ─────────────────────────────────────────────────


def _is_statsmodels(model: Any) -> bool:
    try:
        from statsmodels.base.wrapper import ResultsWrapper

        return isinstance(model, ResultsWrapper)
    except ImportError:
        return False


def _is_pyfixest(model: Any) -> bool:
    try:
        from pyfixest.estimation.feols_ import Feols
        from pyfixest.estimation.fepois_ import Fepois

        return isinstance(model, Feols | Fepois)
    except ImportError:
        return False


def _is_linearmodels(model: Any) -> bool:
    try:
        from linearmodels.iv.results import IVGMMResults, IVResults
        from linearmodels.panel.results import (
            BetweenOLSResults,
            FirstDifferenceOLSResults,
            PanelEffectsResults,
            PooledOLSResults,
            RandomEffectsResults,
        )

        _types = (
            PanelEffectsResults,
            BetweenOLSResults,
            PooledOLSResults,
            RandomEffectsResults,
            FirstDifferenceOLSResults,
            IVResults,
            IVGMMResults,
        )
        return isinstance(model, _types)
    except ImportError:
        return False


# ── statsmodels adapters ──────────────────────────────────────────────────────


def _tidy_statsmodels(model: Any, conf_level: float = 0.95) -> pd.DataFrame:
    alpha = 1.0 - conf_level
    ci = model.conf_int(alpha=alpha)
    return pd.DataFrame(
        {
            "term": list(model.params.index),
            "estimate": model.params.values,
            "std_error": model.bse.values,
            "statistic": model.tvalues.values,
            "p_value": model.pvalues.values,
            "conf_low": ci.iloc[:, 0].values,
            "conf_high": ci.iloc[:, 1].values,
        }
    )


def _glance_statsmodels(model: Any) -> pd.DataFrame:
    mse_resid = getattr(model, "mse_resid", np.nan)
    return pd.DataFrame(
        [
            {
                "nobs": int(model.nobs),
                "r_squared": getattr(model, "rsquared", np.nan),
                "adj_r_squared": getattr(model, "rsquared_adj", np.nan),
                "rmse": np.sqrt(mse_resid) if not np.isnan(mse_resid) else np.nan,
                "f_statistic": getattr(model, "fvalue", np.nan),
                "p_value_f": getattr(model, "f_pvalue", np.nan),
                "df_model": getattr(model, "df_model", np.nan),
                "df_residual": getattr(model, "df_resid", np.nan),
                "estimator": type(model.model).__name__,
                "fixed_effects": "",
                "vcov_type": _sm_vcov_name(model),
            }
        ]
    )


def _sm_vcov_name(model: Any) -> str:
    """Best-effort extraction of variance estimator label from statsmodels."""
    cov_type = getattr(model, "cov_type", None)
    if cov_type:
        return str(cov_type)
    if hasattr(model, "HC0_se"):
        return "HC0"
    return "OLS"


# ── pyfixest adapters ──────────────────────────────────────────────────────────


def _tidy_pyfixest(model: Any, conf_level: float = 0.95) -> pd.DataFrame:
    """
    pyfixest result objects expose a .tidy() method.
    Column names differ slightly by version so we normalise them.
    """
    alpha = 1.0 - conf_level
    try:
        raw = model.tidy(alpha=alpha)
        # pyfixest tidy() columns (as of 0.20+):
        #   Estimate | Std. Error | t value | Pr(>|t|) | 2.5% | 97.5%
        #   Coefficient is in the index, not a column
        raw = raw.reset_index()
        rename = {
            "Coefficient": "term",
            "Estimate": "estimate",
            "Std. Error": "std_error",
            "t value": "statistic",
            "Pr(>|t|)": "p_value",
        }
        raw = raw.rename(columns=rename)
        # CI columns: detect by position (last two numeric cols)
        numeric_unnamed = [c for c in raw.columns if c not in rename.values() and c != "term"]
        if len(numeric_unnamed) >= 2:
            raw = raw.rename(
                columns={
                    numeric_unnamed[-2]: "conf_low",
                    numeric_unnamed[-1]: "conf_high",
                }
            )
        return raw.reset_index(drop=True)
    except Exception:
        # Fallback: manual extraction via public accessors
        coef = model.coef()
        se = model.se()
        ts = model.tstat()
        pv = model.pvalue()
        ci = model.confint(alpha=alpha)
        return pd.DataFrame(
            {
                "term": list(coef.index),
                "estimate": coef.values,
                "std_error": se.values,
                "statistic": ts.values,
                "p_value": pv.values,
                "conf_low": ci.iloc[:, 0].values,
                "conf_high": ci.iloc[:, 1].values,
            }
        )


def _glance_pyfixest(model: Any) -> pd.DataFrame:
    # nobs - get from data dimensions
    nobs = np.nan
    if hasattr(model, "_data") and model._data is not None:
        nobs = len(model._data)

    # R² — try multiple attribute spellings across versions
    r2 = np.nan
    for attr in ("_r2", "r2", "r2_overall"):
        val = getattr(model, attr, None)
        if val is not None:
            r2 = float(val() if callable(val) else val)
            break

    # Adjusted R²
    for attr in ("_adj_r2", "adj_r2", "adj_r2_overall"):
        val = getattr(model, attr, None)
        if val is not None:
            adj_r2 = float(val() if callable(val) else val)
            break
    else:
        adj_r2 = np.nan

    # RMSE
    rmse = np.nan
    for attr in ("_rmse", "rmse"):
        val = getattr(model, attr, None)
        if val is not None:
            rmse = float(val() if callable(val) else val)
            break

    # Fixed effects spec string
    fe = ""
    for attr in ("_fixef", "fixef_", "_fe_formula"):
        val = getattr(model, attr, None)
        if val:
            fe = str(val)
            break

    # VCV type
    vcov = ""
    for attr in ("_vcov_type", "vcov_type", "_cov_type"):
        val = getattr(model, attr, None)
        if val:
            vcov = str(val)
            break

    return pd.DataFrame(
        [
            {
                "nobs": int(nobs) if not np.isnan(float(nobs)) else np.nan,
                "r_squared": r2,
                "adj_r_squared": adj_r2,
                "rmse": float(rmse) if rmse is not None else np.nan,
                "f_statistic": np.nan,
                "p_value_f": np.nan,
                "df_model": np.nan,
                "df_residual": np.nan,
                "estimator": "OLS (FE)" if "Feols" in type(model).__name__ else "Poisson (FE)",
                "fixed_effects": fe,
                "vcov_type": vcov,
            }
        ]
    )


# ── linearmodels adapters ──────────────────────────────────────────────────────


def _tidy_linearmodels(model: Any, conf_level: float = 0.95) -> pd.DataFrame:
    ci = model.conf_int(level=conf_level)
    return pd.DataFrame(
        {
            "term": list(model.params.index),
            "estimate": model.params.values,
            "std_error": model.std_errors.values,
            "statistic": model.tstats.values,
            "p_value": model.pvalues.values,
            "conf_low": ci["lower"].values,
            "conf_high": ci["upper"].values,
        }
    )


def _glance_linearmodels(model: Any) -> pd.DataFrame:
    # linearmodels surfaces F-statistic as a named tuple / dict
    fstat = np.nan
    try:
        fs = model.f_statistic
        fstat = float(fs.stat if hasattr(fs, "stat") else fs)
    except Exception:
        pass

    r2 = np.nan
    for attr in ("rsquared", "rsquared_overall", "rsquared_within"):
        val = getattr(model, attr, None)
        if val is not None and not np.isnan(float(val)):
            r2 = float(val)
            break

    return pd.DataFrame(
        [
            {
                "nobs": int(model.nobs),
                "r_squared": r2,
                "adj_r_squared": np.nan,
                "rmse": np.nan,
                "f_statistic": fstat,
                "p_value_f": np.nan,
                "df_model": np.nan,
                "df_residual": getattr(model, "df_resid", np.nan),
                "estimator": type(model).__name__,
                "fixed_effects": "",
                "vcov_type": str(getattr(model, "cov_type", "")),
            }
        ]
    )
