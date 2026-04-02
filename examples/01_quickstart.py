"""
examples/01_quickstart.py
=========================
Self-contained quickstart — no external data needed.

Run with:
    uv run python examples/01_quickstart.py
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm

import tidyecon as te

rng = np.random.default_rng(42)
n = 200
df = pd.DataFrame(
    {
        "income": rng.normal(50_000, 15_000, n),
        "education": rng.integers(10, 22, n),
        "wages": None,
    }
)
df["wages"] = 5_000 + 0.15 * df["income"] + 300 * df["education"] + rng.normal(0, 2_000, n)

X1 = sm.add_constant(df[["income"]])
X2 = sm.add_constant(df[["income", "education"]])

fit1 = sm.OLS(df["wages"], X1).fit()
fit2 = sm.OLS(df["wages"], X2).fit()
fit2_hc1 = sm.OLS(df["wages"], X2).fit(cov_type="HC1")

# ── tidy() ─────────────────────────────────────────────────────────────────
print("=== tidy(fit2) ===")
print(te.tidy(fit2).to_string(index=False))

# ── glance() ───────────────────────────────────────────────────────────────
print("\n=== glance(fit2) ===")
print(
    te.glance(fit2)[["nobs", "r_squared", "adj_r_squared", "rmse", "f_statistic"]].to_string(
        index=False
    )
)

# ── modelsummary() → HTML ──────────────────────────────────────────────────
html = te.modelsummary(
    {"(1) Income only": fit1, "(2) Full": fit2, "(2) HC1": fit2_hc1},
    coef_map={
        "const": "Intercept",
        "income": "Income",
        "education": "Education (years)",
    },
    title="Wage regressions",
    notes=[
        "OLS estimates. Dependent variable: annual wages.",
        "Column 3 uses HC1 heteroskedasticity-robust standard errors.",
    ],
)
with open("examples/output/table_quickstart.html", "w") as f:
    f.write(html)
print("\nHTML table written to examples/output/table_quickstart.html")

# ── modelsummary() → LaTeX ─────────────────────────────────────────────────
te.modelsummary(
    {"(1)": fit1, "(2)": fit2},
    coef_map={"const": "Intercept", "income": "Income", "education": "Education"},
    output="examples/output/table_quickstart.tex",
)
print("LaTeX table written to examples/output/table_quickstart.tex")

# ── modelsummary() → Word ──────────────────────────────────────────────────
te.modelsummary(
    {"(1)": fit1, "(2)": fit2},
    coef_map={"const": "Intercept", "income": "Income", "education": "Education"},
    output="examples/output/table_quickstart.docx",
)
print("Word table written to examples/output/table_quickstart.docx")
