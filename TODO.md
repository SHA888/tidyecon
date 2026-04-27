# TODO

Tracked tasks for `tidyecon`. Items are grouped by milestone.
Status: `[ ]` open · `[x]` done · `[-]` deferred · `[~]` in progress

---

## Milestone 0 — Scaffold (done)

- [x] Package structure (`src/tidyecon/`)
- [x] `_protocol.py` — canonical `TIDY_COLS` / `GLANCE_COLS` schema
- [x] `_adapters.py` — dispatch `tidy()` / `glance()` for statsmodels
- [x] `_summary.py` — `modelsummary()` core table builder
- [x] `renderers/html.py` — self-contained HTML with academic CSS
- [x] `renderers/latex.py` — booktabs LaTeX output
- [x] `renderers/docx.py` — python-docx Word output
- [x] `validate/fixtures.py` — OLS + Logit hardcoded R benchmarks
- [x] `validate/runner.py` — numerical comparison CLI
- [x] `tests/conftest.py` — inline mtcars fixture (no network)
- [x] `tests/test_adapters.py` — 18 tests for tidy()/glance()
- [x] `tests/test_summary.py` — 22 tests covering all three renderers
- [x] `tests/test_validate.py` — benchmark pass/fail
- [x] `pyproject.toml` with uv + hatchling
- [x] `uv.lock`
- [x] `README.md`
- [x] `TODO.md`
- [x] `CONTRIBUTING.md`
- [x] `LICENSE`
- [x] `.gitignore`
- [x] `.github/workflows/ci.yml`

---

## Milestone 1 — Backend completeness

### 1.1 pyfixest integration tests ✅ COMPLETED
- [x] Add `pyfixest` to dev dependencies in `pyproject.toml` (already listed — verify install)
- [x] Add `tests/test_pyfixest.py`:
  - [x] `test_tidy_feols_basic` — OLS with FE, verify schema
  - [x] `test_tidy_feols_clustered` — CRV1, verify SE differs from iid
  - [x] `test_tidy_fepois` — Poisson FE
  - [x] `test_tidy_feols_iv` — IV via three-part formula
  - [x] `test_glance_feols` — nobs, r2, rmse extraction
  - [x] `test_tidy_ci_width` — conf_level=0.99 > conf_level=0.95
- [x] Add pyfixest validation fixture in `validate/fixtures.py`:
  - [x] `feols_mtcars` — `feols("mpg ~ hp | cyl", data=mtcars)` vs R `fixest::feols`
  - [x] Document R commands used to generate expected values
- [x] Verify `_tidy_pyfixest` CI column detection handles pyfixest ≥ 0.25 column name changes

### 1.2 linearmodels integration tests
- [ ] Add `tests/test_linearmodels.py`:
  - [ ] `test_tidy_panel_ols` — entity FE, verify schema
  - [ ] `test_tidy_pooled_ols` — basic panel
  - [ ] `test_tidy_random_effects` — RE estimator
  - [ ] `test_tidy_iv2sls` — instrumental variables, verify term names
  - [ ] `test_glance_panel` — nobs, r_squared extraction
  - [ ] `test_conf_int_level` — verify conf_int(level=) parameter used correctly
- [ ] Add linearmodels validation fixture in `validate/fixtures.py`:
  - [ ] Panel FE fixture with known data and R/Stata reference values
- [ ] Fix `_glance_linearmodels`: `rsquared_within` vs `rsquared_overall` selection logic

### 1.3 SE / DF correction parity
- [ ] Document the one known numerical discrepancy:
  - `linearmodels` `group_debias=False` default vs Stata small-cluster correction
  - Add a note in `_tidy_linearmodels` docstring
- [ ] Add test `test_se_matches_stata_small_cluster` (fixture with Stata output)
- [ ] Consider exposing `debiased: bool = True` parameter on `tidy()`

---

## Milestone 2 — `modelsummary()` completeness

### 2.1 Rendering fixes
- [ ] `confint` statistic: fix alignment when CI strings have unequal lengths
- [ ] LaTeX: wrap in `threeparttable` environment when `notes` is non-empty
- [ ] LaTeX: add `\label{tab:...}` support via optional `label` parameter
- [ ] HTML: add `id` attribute to `<table>` for CSS targeting
- [ ] docx: expose `font_name` and `font_size` parameters
- [ ] docx: handle multi-line notes (currently joins on single row)

### 2.2 New output formats
- [ ] `output="markdown"` — GitHub-flavoured Markdown table
- [ ] `output="csv"` — flat CSV for programmatic consumption
- [ ] `output="dataframe"` — return raw `pd.DataFrame` of the display grid
- [ ] Quarto `.qmd` integration guide in `docs/`

### 2.3 Mixed model tables
- [ ] Allow mixing statsmodels + pyfixest models in one table
- [ ] Add `test_mixed_backends` test
- [ ] Normalise `fixed_effects` display in GOF rows across backends

### 2.4 Additional GOF statistics
- [ ] Akaike Information Criterion (`aic`) — from statsmodels
- [ ] Bayesian Information Criterion (`bic`) — from statsmodels
- [ ] Log-likelihood (`loglikelihood`)
- [ ] Number of clusters (`n_clusters`) — from pyfixest

---

## Milestone 3 — Validation suite expansion

- [ ] Add R fixtures for all standard mtcars regressions:
  - [ ] `lm(mpg ~ hp)` — simple OLS
  - [ ] `lm(mpg ~ hp + wt + am)` — three regressors
  - [ ] `lm(mpg ~ hp + wt, subset = am == 1)` — subsample
  - [ ] `feols(mpg ~ hp | cyl, data = mtcars)` — FE via fixest
- [ ] Add Stata fixtures (Stata 18):
  - [ ] `reg mpg hp wt, robust` — HC1 robust SEs
  - [ ] `areg mpg hp wt, absorb(cyl) vce(cluster cyl)` — FE + clustering
- [ ] Add panel data fixture using publicly available dataset (e.g. Grunfeld)
- [ ] Add IV fixture using Card (1995) proximity-to-college instrument data
- [ ] `validate/runner.py`: add `--json` flag to output machine-readable results
- [ ] `validate/runner.py`: add `--fixture <name>` flag to run single fixture

---

## Milestone 4 — Docs

- [ ] `docs/architecture.md` — explain protocol, dispatch, renderers
- [ ] `docs/adding_backends.md` — step-by-step guide with template
- [ ] `docs/adding_fixtures.md` — how to generate R values and write fixtures
- [ ] `docs/stata_parity.md` — known numerical equivalences and discrepancies
- [ ] `docs/quarto_workflow.md` — example `.qmd` with tidyecon + Quarto publish
- [ ] Set up MkDocs or Sphinx (decision pending — see note below)
  - Note: MkDocs + Material is lighter; Sphinx is better for API autodoc
  - Recommendation: MkDocs for now, migrate if API grows

---

## Milestone 5 — DX and packaging

- [ ] Add `pyright` config to `pyproject.toml` (`strict` mode on `src/`)
- [ ] Add `ruff` format config (`ruff format` as the formatter)
- [ ] Pre-commit hooks:
  - [ ] `ruff check --fix`
  - [ ] `ruff format`
  - [ ] `pyright` (non-blocking on CI, blocking locally)
- [ ] `CHANGELOG.md` — start with v0.1.0
- [ ] First PyPI release checklist (see below)
- [ ] `examples/01_quickstart.py` — self-contained, runs with `uv run`
- [ ] `examples/02_pyfixest.py` — panel FE workflow
- [ ] `examples/03_linearmodels.py` — IV + panel workflow
- [ ] `examples/04_mixed_table.py` — combining multiple backends

---

## PyPI release checklist (v0.1.0)

- [ ] All Milestone 1 and 2 items complete
- [ ] `uv run pytest` passes with 0 failures and 0 warnings
- [ ] `uv run tidyecon-validate` passes all fixtures
- [ ] `uv run pyright src` — 0 errors
- [ ] `uv run ruff check src tests` — 0 violations
- [ ] `CHANGELOG.md` entry written
- [ ] Version bumped in `pyproject.toml` (`0.1.0`)
- [ ] GitHub tag `v0.1.0` created
- [ ] `uv build && uv publish` — package on PyPI
- [ ] GitHub release created with changelog excerpt

---

## Deferred / out of scope

- [-] Pandas `style` / Jupyter notebook renderer — low priority, pandas already handles this
- [-] Excel output — `great_tables` covers this better
- [-] Bayesian model support (ArviZ) — separate domain, deferred to v0.3
- [-] Survival analysis (`lifelines`) — deferred to v0.2

---

## Future work (deferred from Milestone 1.1 review)

- [ ] **Decide `f_statistic` semantics for `_glance_pyfixest`.** Currently always `np.nan`.
  Touches the public glance schema in `_protocol.py`, `_summary.py`, `validate/fixtures.py`,
  `README.md`, and `examples/01_quickstart.py`, so any change is cross-cutting. Options:
  - drop the column from the global `GLANCE_COLS` schema entirely;
  - compute it via `model.wald_test()` for Feols (verify behavior on Fepois / IV);
  - keep `nan` and document it as the "not available" contract.
- [ ] **Reproducibility comments in `validate/fixtures.py`.** Add the exact R commands
  (`broom::tidy`, `fixest::etable`, `confint`) used to derive each `CoefFixture` /
  `GlanceFixture` value, so future maintainers can regenerate them without guessing.
- [ ] **Rename `test_pyfixest_dispatch_does_not_swallow_statsmodels`** (was
  `test_pyfixest_adapter_error_handling`) is already descriptive, but consider adding
  a real negative-path test: `tidy(object())` should raise `TypeError` from the dispatcher.
