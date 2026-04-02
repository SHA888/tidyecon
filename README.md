# tidyecon

**`broom` + `modelsummary` for Python econometrics.**

tidyecon closes the last gap between Python and Stata/R for applied microeconomics:

- `tidy()` — unified coefficient table from any supported model (mirrors R `broom::tidy`)
- `glance()` — unified model statistics (mirrors R `broom::glance`)
- `modelsummary()` — publication-ready regression tables → HTML, LaTeX, Word (mirrors R `modelsummary`)
- `tidyecon-validate` — CLI numerical benchmark suite against hardcoded R results

Supports **statsmodels**, **pyfixest**, and **linearmodels** via dispatch. Zero modifications to upstream model objects.

---

## Installation

```bash
uv add tidyecon                    # core (statsmodels)
uv add "tidyecon[all]"             # + pyfixest + linearmodels
uv add "tidyecon[pyfixest]"        # individual backend
uv add "tidyecon[linearmodels]"
```

Requires Python ≥ 3.11.

---

## Quick start

```python
import statsmodels.api as sm
import pandas as pd
import tidyecon as te

X      = sm.add_constant(df[["income", "education"]])
fit    = sm.OLS(df["wages"], X).fit()
fit_hc = sm.OLS(df["wages"], X).fit(cov_type="HC1")

te.tidy(fit)     # DataFrame: term, estimate, std_error, statistic, p_value, conf_low, conf_high
te.glance(fit)   # DataFrame: nobs, r_squared, adj_r_squared, rmse, f_statistic, ...

te.modelsummary(
    {"OLS": fit, "OLS (HC1)": fit_hc},
    coef_map={"const": "Intercept", "income": "Income", "educ": "Education"},
    notes=["HC1 robust SEs in column 2."],
    output="table.html",   # or .tex or .docx
)
```

---

## API

### `tidy(model, conf_level=0.95)`

Returns a DataFrame with columns:
`term` · `estimate` · `std_error` · `statistic` · `p_value` · `conf_low` · `conf_high`

Supported backends:

| Backend | Types |
|---|---|
| `statsmodels` | Any `ResultsWrapper` — OLS, WLS, GLS, Logit, Probit, Poisson, … |
| `pyfixest` | `Feols`, `Fepois` |
| `linearmodels` | `PanelOLS`, `PooledOLS`, `RandomEffects`, `BetweenOLS`, `FirstDifferenceOLS`, `IV2SLS`, `IVGMM` |

### `glance(model)`

Returns a single-row DataFrame with model statistics:
`nobs` · `r_squared` · `adj_r_squared` · `rmse` · `f_statistic` · `p_value_f` · `df_model` · `df_residual` · `estimator` · `fixed_effects` · `vcov_type`

### `modelsummary(models, *, stars, statistic, fmt, coef_map, coef_omit, gof_map, title, notes, output)`

| Parameter | Default | Options |
|---|---|---|
| `stars` | `True` | `True` · `False` · `{"***": 0.01, ...}` |
| `statistic` | `"se"` | `"se"` · `"tstat"` · `"pvalue"` · `"confint"` |
| `output` | `"html"` | `"html"` · `"latex"` · `"docx"` · any `*.html`/`*.tex`/`*.docx` path |

```python
# Rename and reorder coefficients (drops terms not in map)
te.modelsummary(models, coef_map={"wt": "Weight", "hp": "Horsepower"})

# Drop intercept
te.modelsummary(models, coef_omit=["const"])

# t-statistics instead of SEs
te.modelsummary(models, statistic="tstat")

# Write directly to file
te.modelsummary(models, output="results/table.docx")
```

---

## Validation

```bash
tidyecon-validate            # run all R benchmarks
tidyecon-validate --verbose  # show every check
```

Compares `tidy()` output against hardcoded R 4.4.1 values (OLS + Logit on mtcars).
Add new fixtures in `src/tidyecon/validate/fixtures.py`.

---

## Development

```bash
git clone https://github.com/yourorg/tidyecon && cd tidyecon
uv sync --extra dev
uv pip install -e .  # Install in editable mode for development
uv run pytest
uv run ruff check src tests
uv run pyright src
uv run tidyecon-validate --verbose
```

**Important setup notes:**
- `uv sync --extra dev` installs all development dependencies including pytest, statsmodels, etc.
- `uv pip install -e .` makes the tidyecon module importable during development
- Tests require statsmodels and other optional dependencies to be installed

See [TODO.md](TODO.md) for the roadmap and [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

---

## License

MIT — see [LICENSE](LICENSE).

**Inspired by:** R [`broom`](https://broom.tidymodels.org/) · R [`modelsummary`](https://vincentarelbundock.github.io/modelsummary/) · [`pyfixest`](https://github.com/py-econometrics/pyfixest)
