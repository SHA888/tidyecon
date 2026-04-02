"""
tests/conftest.py
=================
Shared fixtures.  mtcars is embedded directly — no network fetch.
"""

import pandas as pd
import pytest
import statsmodels.api as sm

# ── Inline mtcars (n=32, standard R dataset) ──────────────────────────────────
_MTCARS_RAW = {
    "mpg": [
        21.0,
        21.0,
        22.8,
        21.4,
        18.7,
        18.1,
        14.3,
        24.4,
        22.8,
        19.2,
        17.8,
        16.4,
        17.3,
        15.2,
        10.4,
        10.4,
        14.7,
        32.4,
        30.4,
        33.9,
        21.5,
        15.5,
        15.2,
        13.3,
        19.2,
        27.3,
        26.0,
        30.4,
        15.8,
        19.7,
        15.0,
        21.4,
    ],
    "cyl": [
        6,
        6,
        4,
        6,
        8,
        6,
        8,
        4,
        4,
        6,
        6,
        8,
        8,
        8,
        8,
        8,
        8,
        4,
        4,
        4,
        6,
        8,
        8,
        8,
        6,
        4,
        4,
        4,
        8,
        6,
        8,
        4,
    ],
    "hp": [
        110,
        110,
        93,
        110,
        175,
        105,
        245,
        62,
        95,
        123,
        123,
        180,
        180,
        180,
        205,
        215,
        230,
        66,
        52,
        65,
        97,
        150,
        150,
        245,
        175,
        66,
        91,
        113,
        264,
        175,
        335,
        109,
    ],
    "wt": [
        2.620,
        2.875,
        2.320,
        3.215,
        3.440,
        3.460,
        3.570,
        3.190,
        3.150,
        3.440,
        3.440,
        4.070,
        3.730,
        3.780,
        5.250,
        5.424,
        5.345,
        2.200,
        1.615,
        1.835,
        2.465,
        3.520,
        3.435,
        3.840,
        3.845,
        1.935,
        2.140,
        1.513,
        3.170,
        2.770,
        3.570,
        2.780,
    ],
    "am": [
        1,
        1,
        1,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
    ],
}


@pytest.fixture(scope="session")
def mtcars() -> pd.DataFrame:
    return pd.DataFrame(_MTCARS_RAW)


@pytest.fixture(scope="session")
def ols_fit(mtcars) -> sm.regression.linear_model.RegressionResultsWrapper:
    X = sm.add_constant(mtcars[["hp", "wt"]])
    return sm.OLS(mtcars["mpg"], X).fit()


@pytest.fixture(scope="session")
def logit_fit(mtcars):
    X = sm.add_constant(mtcars[["hp", "wt"]])
    return sm.Logit(mtcars["am"], X).fit(disp=False)


@pytest.fixture(scope="session")
def ols_hc1(mtcars) -> sm.regression.linear_model.RegressionResultsWrapper:
    X = sm.add_constant(mtcars[["hp", "wt"]])
    return sm.OLS(mtcars["mpg"], X).fit(cov_type="HC1")


@pytest.fixture(scope="session")
def models(mtcars, ols_fit, ols_hc1):
    X1 = sm.add_constant(mtcars[["hp"]])
    fit1 = sm.OLS(mtcars["mpg"], X1).fit()
    return {
        "(1)": fit1,
        "(2)": ols_fit,
        "(2) HC1": ols_hc1,
    }
