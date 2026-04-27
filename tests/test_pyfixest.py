"""
tests/test_pyfixest.py
======================
Integration tests for pyfixest adapter using mtcars dataset.
Tests cover Feols, Fepois, IV, clustering, and CI width variations.
"""

import numpy as np
import pandas as pd
import pytest

from tidyecon import glance, tidy

EXPECTED_TIDY_COLS = [
    "term",
    "estimate",
    "std_error",
    "statistic",
    "p_value",
    "conf_low",
    "conf_high",
]


@pytest.fixture(scope="session")
def feols_basic(mtcars):
    """Basic OLS with fixed effects: mpg ~ hp | cyl"""
    from pyfixest import feols

    return feols("mpg ~ hp | cyl", data=mtcars)


@pytest.fixture(scope="session")
def feols_clustered(mtcars):
    """OLS with clustered SE: mpg ~ hp, cluster by cyl"""
    from pyfixest import feols

    return feols("mpg ~ hp", data=mtcars).vcov({"CRV1": "cyl"})


@pytest.fixture(scope="session")
def fepois_basic(mtcars):
    """Poisson with fixed effects on a count outcome: gear ~ hp | cyl"""
    from pyfixest import fepois

    return fepois("gear ~ hp | cyl", data=mtcars)


@pytest.fixture(scope="session")
def feols_iv(mtcars):
    """IV via three-part formula: outcome mpg, FE cyl, hp instrumented by wt.

    Note: wt is a weak/imperfect instrument for hp on mtcars; this fixture
    exists only to exercise the pyfixest IV code path and verify schema.
    """
    from pyfixest import feols

    return feols("mpg ~ 1 | cyl | hp ~ wt", data=mtcars)


def test_tidy_feols_basic(feols_basic):
    """Test basic Feols with fixed effects, verify schema"""
    result = tidy(feols_basic)

    assert list(result.columns) == EXPECTED_TIDY_COLS

    assert len(result) >= 1
    assert "hp" in result["term"].values

    assert result["estimate"].dtype in [np.float64, np.float32]
    assert result["std_error"].dtype in [np.float64, np.float32]
    assert result["p_value"].dtype in [np.float64, np.float32]

    hp_coef = result[result["term"] == "hp"]["estimate"].iloc[0]
    assert hp_coef < 0  # hp should negatively affect mpg


def test_tidy_feols_clustered(mtcars, feols_clustered):
    """Test clustered SE, verify SE differs from iid"""
    from pyfixest import feols

    feols_iid = feols("mpg ~ hp", data=mtcars)

    clustered_result = tidy(feols_clustered)
    iid_result = tidy(feols_iid)

    hp_clustered = clustered_result[clustered_result["term"] == "hp"]["std_error"].iloc[0]
    hp_iid = iid_result[iid_result["term"] == "hp"]["std_error"].iloc[0]

    assert hp_clustered != hp_iid
    assert hp_clustered > 0 and hp_iid > 0


def test_tidy_fepois(fepois_basic):
    """Test Poisson FE model on a count outcome (gear)."""
    result = tidy(fepois_basic)

    assert list(result.columns) == EXPECTED_TIDY_COLS
    assert "hp" in result["term"].values

    hp_coef = result[result["term"] == "hp"]["estimate"].iloc[0]
    assert np.isfinite(hp_coef)

    hp_se = result[result["term"] == "hp"]["std_error"].iloc[0]
    assert hp_se > 0


def test_tidy_feols_iv(feols_iv):
    """Test IV via three-part formula: instrumented coefficient appears."""
    result = tidy(feols_iv)

    assert list(result.columns) == EXPECTED_TIDY_COLS

    # The instrumented variable hp must appear as a term.
    assert "hp" in result["term"].values

    hp_coef = result[result["term"] == "hp"]["estimate"].iloc[0]
    assert np.isfinite(hp_coef)

    hp_se = result[result["term"] == "hp"]["std_error"].iloc[0]
    assert hp_se > 0


def test_glance_feols(feols_basic):
    """Test glance extraction: nobs, r2, adj_r2, rmse."""
    result = glance(feols_basic)

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 1

    # Required schema columns must be present unconditionally.
    for col in ("nobs", "r_squared", "adj_r_squared", "rmse"):
        assert col in result.columns, f"missing column: {col}"

    nobs = result["nobs"].iloc[0]
    assert isinstance(nobs, int | float | np.integer | np.floating)
    assert nobs == 32

    r2 = result["r_squared"].iloc[0]
    assert isinstance(r2, int | float)
    assert 0 <= r2 <= 1

    adj_r2 = result["adj_r_squared"].iloc[0]
    assert isinstance(adj_r2, int | float)
    assert adj_r2 <= r2

    rmse = result["rmse"].iloc[0]
    assert isinstance(rmse, int | float)
    assert rmse > 0


def test_tidy_ci_width(mtcars):
    """Test CI width: conf_level=0.99 > conf_level=0.95"""
    from pyfixest import feols

    model = feols("mpg ~ hp", data=mtcars)

    result_95 = tidy(model, conf_level=0.95)
    result_99 = tidy(model, conf_level=0.99)

    assert len(result_95) == len(result_99)

    for term in result_95["term"]:
        row_95 = result_95[result_95["term"] == term].iloc[0]
        row_99 = result_99[result_99["term"] == term].iloc[0]

        width_95 = row_95["conf_high"] - row_95["conf_low"]
        width_99 = row_99["conf_high"] - row_99["conf_low"]

        assert (
            width_99 > width_95
        ), f"CI width for {term}: 99% ({width_99}) should be > 95% ({width_95})"


def test_pyfixest_dispatch_does_not_swallow_statsmodels():
    """tidy() should still dispatch correctly to statsmodels even when pyfixest is installed."""
    import statsmodels.api as sm

    rng = np.random.default_rng(0)
    n = 50
    df = pd.DataFrame({"y": rng.normal(size=n), "x": rng.normal(size=n)})
    sm_model = sm.OLS(df["y"], sm.add_constant(df[["x"]])).fit()

    result = tidy(sm_model)
    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == EXPECTED_TIDY_COLS
