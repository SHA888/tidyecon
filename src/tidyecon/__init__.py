# src/tidyecon/__init__.py
"""
tidyecon
========
Unified tidy interface and publication-ready regression tables
for Python econometrics.

Quick start
-----------
    import statsmodels.api as sm
    from statsmodels.datasets import get_rdataset
    import tidyecon as te

    mtcars = get_rdataset('mtcars', 'datasets').data
    X      = sm.add_constant(mtcars[['hp', 'wt']])
    fit    = sm.OLS(mtcars['mpg'], X).fit()

    te.tidy(fit)          # DataFrame of coefficients
    te.glance(fit)        # DataFrame of model stats
    te.modelsummary(      # publication table
        {"Base": fit},
        output="table.html"
    )
"""
from ._adapters import glance, tidy
from ._summary  import modelsummary

__all__ = ["tidy", "glance", "modelsummary"]
__version__ = "0.1.0"
