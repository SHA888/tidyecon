"""
examples/02_pyfixest.py
=======================
pyfixest panel regression with tidyecon.

Requires: uv add "tidyecon[pyfixest]"

Run with:
    uv run python examples/02_pyfixest.py
"""
try:
    import pyfixest as pf
except ImportError:
    raise SystemExit(
        "pyfixest not installed. Run: uv add 'tidyecon[pyfixest]'"
    )

import pandas as pd
import tidyecon as te

# pyfixest ships a built-in dataset
data = pf.get_data()

# OLS with two-way FE and CRV1 clustered SEs
fit_fe   = pf.feols("Y ~ X1 | f1 + f2",  data=data, vcov="CRV1")
fit_iv   = pf.feols("Y ~ 1 | f1 | X1 ~ Z1", data=data)
fit_pois = pf.fepois("Y ~ X1 | f1",       data=data)

# All three go through the same interface
print("=== tidy (FE OLS) ===")
print(te.tidy(fit_fe))

print("\n=== tidy (IV) ===")
print(te.tidy(fit_iv))

print("\n=== glance (FE OLS) ===")
print(te.glance(fit_fe))

# Publication table
te.modelsummary(
    {"FE OLS": fit_fe, "IV": fit_iv, "Poisson FE": fit_pois},
    coef_map={"X1": "Treatment"},
    gof_map=["nobs", "r_squared", "fixed_effects", "vcov_type"],
    output="examples/output/table_pyfixest.html",
)
print("\nTable written to examples/output/table_pyfixest.html")
