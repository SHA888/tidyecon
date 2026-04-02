# Contributing to tidyecon

Contributions welcome. This document covers the dev setup, conventions, and
the most impactful areas to contribute.

---

## Setup

```bash
git clone https://github.com/yourorg/tidyecon
cd tidyecon
uv sync --extra dev
```

Verify everything works:

```bash
uv run pytest                        # 43 tests, all green
uv run tidyecon-validate --verbose   # numerical benchmarks
uv run ruff check src tests          # linter
```

---

## Most impactful contributions

### 1. Validation fixtures

The highest-value contribution is adding hardcoded R or Stata benchmarks.
This directly addresses the trust gap that keeps researchers on Stata.

**To add an R fixture:**

```r
# Run in R — record output exactly
library(broom)
fit <- lm(mpg ~ hp + wt, data = mtcars)
print(tidy(fit, conf.int = TRUE), digits = 10)
print(glance(fit), digits = 10)
```

Then add to `src/tidyecon/validate/fixtures.py`:

```python
MY_FIXTURE = ModelFixture(
    name="ols_short_name",
    description="Human-readable description",
    source="R 4.4.1 lm(mpg ~ hp + wt, data = mtcars)",
    model_factory=(
        "import statsmodels.api as sm\n"
        "# ... inline data or load from tests/data/\n"
        "model = sm.OLS(y, X).fit()"
    ),
    coefs=[
        CoefFixture("const", estimate=37.2272, std_error=1.5988,
                    statistic=23.285, p_value=2.565e-20,
                    conf_low_95=34.002, conf_high_95=40.453),
        # ...
    ],
    glance=GlanceFixture(nobs=32, r_squared=0.82680, adj_r_squared=0.81484),
    tol_coef=1e-4,
    tol_se=1e-4,
)
```

### 2. Backend adapters

If you use `pyfixest`, `linearmodels`, or another econometrics package and
the existing adapter is producing wrong output, please open an issue or PR.

See `_adapters.py` — each backend needs:
- `_is_<backend>(model) -> bool` — lazy type guard
- `_tidy_<backend>(model, conf_level) -> pd.DataFrame` — conforming to TIDY_COLS
- `_glance_<backend>(model) -> pd.DataFrame` — conforming to GLANCE_COLS

### 3. Renderer fixes

The LaTeX and docx renderers have known gaps (see TODO.md §2.1).
These are well-scoped, test-driven changes.

---

## Code conventions

- **Type hints** on all public functions. Run `uv run pyright src`.
- **Docstrings** on all public functions (NumPy style).
- **Tests first** — add a failing test before fixing a bug.
- **No internet in tests** — embed any required data inline (see `tests/conftest.py`).
- **Tolerance, not equality** — numerical tests use `abs(a - b) < tol`, not `==`.

---

## Running tests

```bash
uv run pytest                          # all tests
uv run pytest tests/test_adapters.py  # one file
uv run pytest -k "tidy"               # by keyword
uv run pytest -v --tb=short           # verbose short traceback
```

---

## Pull request checklist

- [ ] `uv run pytest` — 0 failures
- [ ] `uv run ruff check src tests` — 0 violations
- [ ] New functionality has tests
- [ ] Numerical changes have a fixture or tolerance justification
- [ ] `TODO.md` updated if an item is completed
