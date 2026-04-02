# Adding a new backend

This guide walks through adding support for a new econometrics package.
The pattern is consistent regardless of the upstream library.

---

## Step 1 — Type guard

Add a lazy-import `isinstance` check in `src/tidyecon/_adapters.py`:

```python
def _is_mypackage(model: Any) -> bool:
    try:
        from mypackage import MyResultClass, MyOtherResult
        return isinstance(model, (MyResultClass, MyOtherResult))
    except ImportError:
        return False
```

Use lazy imports so that a missing optional dependency only raises an error
when the user actually tries to use that backend, not at import time.

---

## Step 2 — Register in dispatch

Add the guard to `_dispatch_tidy` and `_dispatch_glance`:

```python
def _dispatch_tidy(model: Any):
    if _is_statsmodels(model): return _tidy_statsmodels
    if _is_pyfixest(model):    return _tidy_pyfixest
    if _is_linearmodels(model):return _tidy_linearmodels
    if _is_mypackage(model):   return _tidy_mypackage   # ← add here
    raise TypeError(...)
```

---

## Step 3 — Implement `_tidy_<backend>`

The function must return a DataFrame. The schema validator will enforce
`TIDY_COLS` automatically after your function returns — you do not need to
worry about column order or missing columns.

```python
def _tidy_mypackage(model: Any, conf_level: float = 0.95) -> pd.DataFrame:
    """
    Extract coefficient table from MyPackage result object.

    Notes
    -----
    Matches Stata `reg` output to within 1e-5. See docs/stata_parity.md.
    Known discrepancy: small-sample cluster correction differs from Stata
    when n_clusters < 50 — set group_debias=True to match.
    """
    alpha = 1.0 - conf_level
    ci    = model.conf_int(alpha=alpha)   # adapt to your package's API

    return pd.DataFrame({
        "term":      list(model.params.index),
        "estimate":  model.params.values,
        "std_error": model.std_errors.values,
        "statistic": model.tstats.values,
        "p_value":   model.pvalues.values,
        "conf_low":  ci["lower"].values,
        "conf_high": ci["upper"].values,
    })
```

If the upstream API is unstable across versions, use `try/except` or `getattr`
with defaults:

```python
se = getattr(model, "std_errors", None) or getattr(model, "bse", None)
```

---

## Step 4 — Implement `_glance_<backend>`

```python
def _glance_mypackage(model: Any) -> pd.DataFrame:
    return pd.DataFrame([{
        "nobs":          int(model.nobs),
        "r_squared":     getattr(model, "rsquared", np.nan),
        "adj_r_squared": getattr(model, "rsquared_adj", np.nan),
        "rmse":          np.nan,   # fill in if available
        "f_statistic":   np.nan,
        "p_value_f":     np.nan,
        "df_model":      np.nan,
        "df_residual":   np.nan,
        "estimator":     type(model).__name__,
        "fixed_effects": "",
        "vcov_type":     str(getattr(model, "cov_type", "")),
    }])
```

---

## Step 5 — Add to optional dependencies

In `pyproject.toml`:

```toml
[project.optional-dependencies]
mypackage = ["mypackage>=1.0"]
all = [
    "statsmodels>=0.14",
    "pyfixest>=0.20",
    "linearmodels>=6.0",
    "mypackage>=1.0",    # ← add here
]
```

---

## Step 6 — Add a validation fixture

Generate expected values in R or Stata. See `CONTRIBUTING.md` for the
exact R commands and fixture format.

At minimum, one fixture covering the most common use case of the new backend.

---

## Step 7 — Write tests

Add `tests/test_<backend>.py` covering:

- `test_tidy_schema` — columns match `TIDY_COLS`
- `test_tidy_nrow` — one row per parameter
- `test_conf_low_lt_conf_high`
- `test_p_values_unit_interval`
- `test_conf_level_affects_width`
- `test_glance_schema` — columns match `GLANCE_COLS`
- `test_nobs_correct`
- Numerical test against your fixture

---

## Checklist

- [ ] `_is_<backend>` added with lazy import
- [ ] Registered in `_dispatch_tidy` and `_dispatch_glance`
- [ ] `_tidy_<backend>` returns TIDY_COLS-compatible DataFrame
- [ ] `_glance_<backend>` returns GLANCE_COLS-compatible DataFrame
- [ ] Optional dependency added to `pyproject.toml`
- [ ] Validation fixture added to `validate/fixtures.py`
- [ ] Tests added to `tests/test_<backend>.py`
- [ ] Numerical discrepancies (if any) documented in `docs/stata_parity.md`
- [ ] `TODO.md` updated
