"""
examples/03_linearmodels.py
===========================
linearmodels panel and IV regression with tidyecon.

Requires: uv add "tidyecon[linearmodels]"

Run with:
    uv run python examples/03_linearmodels.py
"""
try:
    from linearmodels.panel import PanelOLS, RandomEffects
    from linearmodels.iv  import IV2SLS
except ImportError:
    raise SystemExit(
        "linearmodels not installed. Run: uv add 'tidyecon[linearmodels]'"
    )

import numpy as np
import pandas as pd
import tidyecon as te

rng   = np.random.default_rng(0)
n_ent = 50
n_t   = 10
N     = n_ent * n_t

entity = np.repeat(np.arange(n_ent), n_t)
time   = np.tile(np.arange(n_t), n_ent)

df = pd.DataFrame({
    "entity": entity,
    "time":   time,
    "x":      rng.normal(size=N),
    "z":      rng.normal(size=N),   # instrument
    "y":      None,
})
df["y"] = 2.5 * df["x"] + rng.normal(0, 0.5, N)
df      = df.set_index(["entity", "time"])

# Panel OLS with entity and time FE
fit_fe = PanelOLS.from_formula(
    "y ~ x + EntityEffects + TimeEffects", data=df
).fit(cov_type="clustered", cluster_entity=True)

# Random effects
fit_re = RandomEffects.from_formula("y ~ x", data=df).fit()

# IV (x instrumented by z)
fit_iv = IV2SLS.from_formula(
    "y ~ 1 + [x ~ z]", data=df.reset_index()
).fit(cov_type="robust")

print("=== tidy (Panel FE) ===")
print(te.tidy(fit_fe))

print("\n=== tidy (IV) ===")
print(te.tidy(fit_iv))

te.modelsummary(
    {"Panel FE": fit_fe, "RE": fit_re, "IV": fit_iv},
    coef_map={"x": "X (treatment)"},
    gof_map=["nobs", "r_squared"],
    output="examples/output/table_linearmodels.html",
)
print("\nTable written to examples/output/table_linearmodels.html")
