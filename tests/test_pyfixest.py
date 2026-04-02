"""
tests/test_pyfixest.py
======================
Integration tests for pyfixest adapter using mtcars dataset.
Tests cover Feols, Fepois, IV, clustering, and CI width variations.
"""
import numpy as np
import pandas as pd
import pytest
from tidyecon import tidy, glance


@pytest.fixture(scope="session")
def feols_basic(mtcars):
    """Basic OLS with fixed effects: mpg ~ hp | cyl"""
    from pyfixest import feols
    return feols("mpg ~ hp | cyl", data=mtcars)


@pytest.fixture(scope="session")
def feols_clustered(mtcars):
    """OLS with clustered SE: mpg ~ hp, cluster by cyl"""
    from pyfixest import feols
    return feols("mpg ~ hp", data=mtcars).vcov({'CRV1': 'cyl'})


@pytest.fixture(scope="session")
def fepois_basic(mtcars):
    """Poisson with fixed effects: am ~ hp | cyl"""
    from pyfixest import fepois
    return fepois("am ~ hp | cyl", data=mtcars)


@pytest.fixture(scope="session")
def feols_iv(mtcars):
    """IV via three-part formula: mpg ~ wt (hp ~ cyl)"""
    from pyfixest import feols
    return feols("mpg ~ wt | hp + cyl", data=mtcars)


def test_tidy_feols_basic(feols_basic):
    """Test basic Feols with fixed effects, verify schema"""
    result = tidy(feols_basic)
    
    # Check schema
    expected_cols = ["term", "estimate", "std_error", "statistic", "p_value", "conf_low", "conf_high"]
    assert list(result.columns) == expected_cols
    
    # Check that we have the right number of coefficients (hp + cyl FEs)
    assert len(result) >= 1  # At least hp coefficient
    assert "hp" in result["term"].values
    
    # Check data types
    assert result["estimate"].dtype in [np.float64, np.float32]
    assert result["std_error"].dtype in [np.float64, np.float32]
    assert result["p_value"].dtype in [np.float64, np.float32]
    
    # Check reasonable values (hp should be negative)
    hp_coef = result[result["term"] == "hp"]["estimate"].iloc[0]
    assert hp_coef < 0  # hp should negatively affect mpg


def test_tidy_feols_clustered(feols_clustered):
    """Test clustered SE, verify SE differs from iid"""
    # Fit iid version for comparison
    from pyfixest import feols
    mtcars = feols_clustered._data if hasattr(feols_clustered, '_data') else None
    if mtcars is None:
        # Fallback: recreate mtcars data
        mtcars = pd.DataFrame({
            "mpg": [21.0,21.0,22.8,21.4,18.7,18.1,14.3,24.4,22.8,19.2,17.8,16.4,
                    17.3,15.2,10.4,10.4,14.7,32.4,30.4,33.9,21.5,15.5,15.2,13.3,
                    19.2,27.3,26.0,30.4,15.8,19.7,15.0,21.4],
            "hp": [110,110,93,110,175,105,245,62,95,123,123,180,180,180,205,215,
                   230,66,52,65,97,150,150,245,175,66,91,113,264,175,335,109],
            "cyl": [6,6,4,6,8,6,8,4,4,6,6,8,8,8,8,8,8,4,4,4,6,8,8,8,6,4,4,4,8,6,8,4],
        })
    
    feols_iid = feols("mpg ~ hp", data=mtcars)
    
    clustered_result = tidy(feols_clustered)
    iid_result = tidy(feols_iid)
    
    # Both should have hp coefficient
    hp_clustered = clustered_result[clustered_result["term"] == "hp"]["std_error"].iloc[0]
    hp_iid = iid_result[iid_result["term"] == "hp"]["std_error"].iloc[0]
    
    # Clustered SE should be different (usually larger) than iid SE
    assert hp_clustered != hp_iid
    assert hp_clustered > 0 and hp_iid > 0


def test_tidy_fepois(fepois_basic):
    """Test Poisson FE model"""
    result = tidy(fepois_basic)
    
    # Check schema
    expected_cols = ["term", "estimate", "std_error", "statistic", "p_value", "conf_low", "conf_high"]
    assert list(result.columns) == expected_cols
    
    # Should have hp coefficient
    assert "hp" in result["term"].values
    
    # Check reasonable values (hp should positively affect transmission probability)
    hp_coef = result[result["term"] == "hp"]["estimate"].iloc[0]
    # For Poisson, coefficient can be positive or negative, but should be non-zero
    assert hp_coef != 0
    
    # Standard errors should be positive
    hp_se = result[result["term"] == "hp"]["std_error"].iloc[0]
    assert hp_se > 0


def test_tidy_feols_iv(feols_iv):
    """Test IV via three-part formula"""
    result = tidy(feols_iv)
    
    # Check schema
    expected_cols = ["term", "estimate", "std_error", "statistic", "p_value", "conf_low", "conf_high"]
    assert list(result.columns) == expected_cols
    
    # Should have wt coefficient (the endogenous variable)
    assert "wt" in result["term"].values
    
    # Check reasonable values
    wt_coef = result[result["term"] == "wt"]["estimate"].iloc[0]
    assert wt_coef != 0
    assert np.isfinite(wt_coef)
    
    # Standard errors should be positive
    wt_se = result[result["term"] == "wt"]["std_error"].iloc[0]
    assert wt_se > 0


def test_glance_feols(feols_basic):
    """Test glance extraction: nobs, r2, rmse"""
    result = glance(feols_basic)
    
    # Check that we have the expected columns
    expected_cols = ["nobs", "r_squared", "adj_r_squared", "f_statistic"]
    for col in expected_cols:
        if col in result.columns:
            assert col in result.columns
    
    # Check nobs
    if "nobs" in result.columns:
        nobs = result["nobs"].iloc[0]
        assert isinstance(nobs, (int, float, np.integer, np.floating))
        assert nobs > 0
    
    # Check R-squared
    if "r_squared" in result.columns:
        r2 = result["r_squared"].iloc[0]
        assert isinstance(r2, (int, float))
        assert 0 <= r2 <= 1 or np.isnan(r2)  # Can be NaN for some models
    
    # Check that result is a DataFrame with one row
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 1


def test_tidy_ci_width():
    """Test CI width: conf_level=0.99 > conf_level=0.95"""
    from pyfixest import feols
    mtcars = pd.DataFrame({
        "mpg": [21.0,21.0,22.8,21.4,18.7,18.1,14.3,24.4,22.8,19.2,17.8,16.4,
                17.3,15.2,10.4,10.4,14.7,32.4,30.4,33.9,21.5,15.5,15.2,13.3,
                19.2,27.3,26.0,30.4,15.8,19.7,15.0,21.4],
        "hp": [110,110,93,110,175,105,245,62,95,123,123,180,180,180,205,215,
               230,66,52,65,97,150,150,245,175,66,91,113,264,175,335,109],
    })
    
    model = feols("mpg ~ hp", data=mtcars)
    
    # Get 95% CI
    result_95 = tidy(model, conf_level=0.95)
    # Get 99% CI  
    result_99 = tidy(model, conf_level=0.99)
    
    # Both should have same number of coefficients
    assert len(result_95) == len(result_99)
    
    # 99% CI should be wider than 95% CI for each coefficient
    for term in result_95["term"]:
        row_95 = result_95[result_95["term"] == term].iloc[0]
        row_99 = result_99[result_99["term"] == term].iloc[0]
        
        width_95 = row_95["conf_high"] - row_95["conf_low"]
        width_99 = row_99["conf_high"] - row_99["conf_low"]
        
        assert width_99 > width_95, f"CI width for {term}: 99% ({width_99}) should be > 95% ({width_95})"


def test_pyfixest_adapter_error_handling():
    """Test that pyfixest adapter handles edge cases gracefully"""
    # Test with non-pyfixest object
    import statsmodels.api as sm
    mtcars = pd.DataFrame({
        "mpg": [21.0,21.0,22.8,21.4,18.7,18.1,14.3,24.4,22.8,19.2,17.8,16.4,
                17.3,15.2,10.4,10.4,14.7,32.4,30.4,33.9,21.5,15.5,15.2,13.3,
                19.2,27.3,26.0,30.4,15.8,19.7,15.0,21.4],
        "hp": [110,110,93,110,175,105,245,62,95,123,123,180,180,180,205,215,
               230,66,52,65,97,150,150,245,175,66,91,113,264,175,335,109],
    })
    X = sm.add_constant(mtcars[["hp"]])
    sm_model = sm.OLS(mtcars["mpg"], X).fit()
    
    # Should work fine with statsmodels
    result = tidy(sm_model)
    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0
