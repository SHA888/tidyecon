# Stata / R parity

This document records known numerical equivalences and discrepancies between
tidyecon output and Stata 18 / R 4.4.1. It is a living document — add a row
whenever you verify or discover a divergence.

---

## statsmodels adapter

| Method | Stata equivalent | Status | Notes |
|---|---|---|---|
| `sm.OLS().fit()` | `reg y x` | ✓ Equivalent | OLS, homoskedastic SE |
| `sm.OLS().fit(cov_type="HC0")` | `reg y x, vce(hc0)` | ✓ Equivalent | |
| `sm.OLS().fit(cov_type="HC1")` | `reg y x, robust` | ✓ Equivalent | Stata `robust` = HC1 |
| `sm.OLS().fit(cov_type="HC2")` | — | ✓ Equivalent | Stata has no direct HC2 shortcut |
| `sm.OLS().fit(cov_type="HC3")` | — | ✓ Equivalent | |
| `sm.OLS().fit(cov_type="cluster", cov_kwds={"groups": g})` | `reg y x, vce(cluster g)` | ✓ Equivalent | One-way cluster |
| `sm.Logit().fit()` | `logit y x` | ✓ Equivalent | z-statistics, not t |
| `sm.Probit().fit()` | `probit y x` | ✓ Equivalent | |
| `sm.Poisson().fit()` | `poisson y x` | ✓ Equivalent | |

### Known discrepancy: OLS F-statistic

statsmodels reports a model F-statistic using `df_model` as numerator degrees
of freedom. Stata uses `e(df_m)` which excludes the constant. For most models
these are the same, but for `noconstant` models they differ by 1.

---

## pyfixest adapter

| Method | Stata equivalent | Status | Notes |
|---|---|---|---|
| `feols("y ~ x \| fe", vcov="iid")` | `xtreg y x, fe` | ✓ Equivalent | Point estimates |
| `feols("y ~ x \| fe", vcov="CRV1")` | `xtreg y x, fe vce(cluster id)` | ✓ Equivalent | One-way cluster |
| `feols("y ~ x \| fe1 + fe2", vcov="CRV1")` | `reghdfe y x, absorb(fe1 fe2) vce(cluster id)` | ✓ Equivalent | Two-way FE |
| `feols("y ~ 1 \| fe \| x ~ z")` | `ivregress 2sls y (x=z), absorb(fe)` | ~ Equivalent | Minor DF differences |

### Known discrepancy: wild bootstrap p-values

pyfixest's wild bootstrap uses a different seed convention than Stata's
`boottest`. Results will differ between runs and implementations unless the
seed is explicitly fixed and both tools use the same bootstrap variant.

---

## linearmodels adapter

| Method | Stata equivalent | Status | Notes |
|---|---|---|---|
| `PanelOLS(..., entity_effects=True).fit()` | `xtreg y x, fe` | ✓ Equivalent | Point estimates |
| `PanelOLS(...).fit(cov_type="clustered", cluster_entity=True)` | `xtreg y x, fe vce(cluster id)` | ⚠ Near equivalent | See note below |
| `RandomEffects.fit()` | `xtreg y x, re` | ✓ Equivalent | |
| `IV2SLS.fit()` | `ivregress 2sls y (x=z)` | ✓ Equivalent | |

### Known discrepancy: small-sample cluster correction

linearmodels defaults to `group_debias=False`, meaning it does **not** apply
the small-sample degrees-of-freedom adjustment that Stata applies by default
(`vce(cluster)`). To match Stata:

```python
result = PanelOLS(...).fit(
    cov_type="clustered",
    cluster_entity=True,
    group_debias=True,   # ← matches Stata default
)
```

Without `group_debias=True`, standard errors will be slightly smaller than
Stata's when the number of clusters is small (< 50). With large cluster counts
(> 200) the difference is negligible.

This discrepancy is documented in `_adapters.py::_tidy_linearmodels`.

---

## How to verify equivalence

**Against R:**
```r
library(broom)
fit <- lm(mpg ~ hp + wt, data = mtcars)
tidy(fit, conf.int = TRUE)
```

**Against Stata:**
```stata
sysuse auto
reg mpg weight trunk
```

Compare the output to `te.tidy(model)` and record the result in this document.
Tolerance for "equivalent": absolute difference < 1e-4 for estimates and SEs.
