"""
tests/test_adapters.py
======================
Tests that tidy() and glance() return correctly shaped, correctly
typed DataFrames for each supported backend.
"""
import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm

import tidyecon as te
from tidyecon._protocol import GLANCE_COLS, TIDY_COLS

# Fixtures: mtcars, ols_fit, logit_fit, ols_hc1 injected from conftest.py


# ── tidy() schema tests ───────────────────────────────────────────────────────

class TestTidySchema:
    def test_columns_present(self, ols_fit):
        df = te.tidy(ols_fit)
        assert list(df.columns) == TIDY_COLS

    def test_returns_dataframe(self, ols_fit):
        assert isinstance(te.tidy(ols_fit), pd.DataFrame)

    def test_nrow_equals_nparams(self, ols_fit):
        df = te.tidy(ols_fit)
        assert len(df) == len(ols_fit.params)

    def test_term_dtype_is_object(self, ols_fit):
        df = te.tidy(ols_fit)
        # pandas >= 2.0 may use StringDtype; both are valid string types
        assert pd.api.types.is_string_dtype(df["term"]) or df["term"].dtype == object

    def test_numeric_cols_are_float(self, ols_fit):
        df = te.tidy(ols_fit)
        for col in ["estimate", "std_error", "statistic", "p_value", "conf_low", "conf_high"]:
            assert pd.api.types.is_float_dtype(df[col]), f"{col} not float"

    def test_conf_low_lt_conf_high(self, ols_fit):
        df = te.tidy(ols_fit)
        assert (df["conf_low"] < df["conf_high"]).all()

    def test_p_values_in_unit_interval(self, ols_fit):
        df = te.tidy(ols_fit)
        assert ((df["p_value"] >= 0) & (df["p_value"] <= 1)).all()

    def test_conf_level_affects_ci_width(self, ols_fit):
        df_95 = te.tidy(ols_fit, conf_level=0.95)
        df_99 = te.tidy(ols_fit, conf_level=0.99)
        width_95 = (df_95["conf_high"] - df_95["conf_low"]).mean()
        width_99 = (df_99["conf_high"] - df_99["conf_low"]).mean()
        assert width_99 > width_95


# ── tidy() numerical accuracy against R ──────────────────────────────────────

class TestTidyNumerical:
    """Values from R: broom::tidy(lm(mpg ~ hp + wt, data=mtcars))"""

    def test_intercept_estimate(self, ols_fit):
        df = te.tidy(ols_fit)
        row = df[df["term"] == "const"].iloc[0]
        assert abs(row["estimate"] - 37.22727) < 1e-4

    def test_hp_estimate(self, ols_fit):
        df = te.tidy(ols_fit)
        row = df[df["term"] == "hp"].iloc[0]
        assert abs(row["estimate"] - (-0.03177)) < 1e-4

    def test_wt_se(self, ols_fit):
        df = te.tidy(ols_fit)
        row = df[df["term"] == "wt"].iloc[0]
        assert abs(row["std_error"] - 0.63273) < 1e-4

    def test_logit_intercept(self, logit_fit):
        df = te.tidy(logit_fit)
        row = df[df["term"] == "const"].iloc[0]
        assert abs(row["estimate"] - 18.866) < 0.01

    def test_robust_se_differs_from_ols(self, ols_fit, ols_hc1):
        df_ols = te.tidy(ols_fit)
        df_hc1 = te.tidy(ols_hc1)
        # HC1 SEs should differ from OLS SEs
        assert not np.allclose(
            df_ols["std_error"].values,
            df_hc1["std_error"].values,
            atol=1e-8,
        )


# ── glance() tests ────────────────────────────────────────────────────────────

class TestGlance:
    def test_columns_present(self, ols_fit):
        df = te.glance(ols_fit)
        assert list(df.columns) == GLANCE_COLS

    def test_single_row(self, ols_fit):
        df = te.glance(ols_fit)
        assert len(df) == 1

    def test_nobs(self, ols_fit, mtcars):
        df = te.glance(ols_fit)
        assert df.iloc[0]["nobs"] == len(mtcars)

    def test_r_squared(self, ols_fit):
        df = te.glance(ols_fit)
        assert abs(df.iloc[0]["r_squared"] - 0.82680) < 1e-4

    def test_adj_r_squared(self, ols_fit):
        df = te.glance(ols_fit)
        assert abs(df.iloc[0]["adj_r_squared"] - 0.81484) < 1e-4


# ── Unsupported model raises cleanly ─────────────────────────────────────────

def test_unknown_model_raises():
    with pytest.raises(TypeError, match="no tidy\\(\\) adapter"):
        te.tidy(object())
