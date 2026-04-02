# Architecture

## Overview

tidyecon has three layers:

```
User code
    │
    ▼
Public API          __init__.py        tidy(), glance(), modelsummary()
    │
    ▼
Protocol layer      _protocol.py       TIDY_COLS, GLANCE_COLS, SummaryTable, TableRow
    │
    ├──────────────────────────────────────────────────┐
    ▼                                                  ▼
Adapter layer       _adapters.py       Summary builder    _summary.py
tidy(), glance()    dispatch +                             modelsummary()
                    per-backend                            builds SummaryTable
                    implementations
                                                           │
                                           ┌───────────────┼───────────────┐
                                           ▼               ▼               ▼
                                      renderers/       renderers/      renderers/
                                      html.py          latex.py        docx.py
```

---

## Protocol layer (`_protocol.py`)

Defines the **canonical output schemas** that every adapter must produce.

### `TIDY_COLS`

```python
["term", "estimate", "std_error", "statistic", "p_value", "conf_low", "conf_high"]
```

Every adapter's `tidy()` return value is passed through `_validate_tidy()`,
which enforces this schema — adding NaN columns if missing, dropping extras,
reordering. This means downstream code (the summary builder, tests, user code)
can rely on these column names unconditionally.

### `GLANCE_COLS`

```python
["nobs", "r_squared", "adj_r_squared", "rmse", "f_statistic",
 "p_value_f", "df_model", "df_residual", "estimator", "fixed_effects", "vcov_type"]
```

Same guarantee. Missing statistics are NaN; string fields default to `""`.

### `SummaryTable`

The intermediate representation consumed by all renderers:

```python
@dataclass
class SummaryTable:
    col_labels:   list[str]       # e.g. ["(1)", "(2)", "(3)"]
    rows:         list[TableRow]  # coefficient rows, stat rows, separators, GOF rows
    title:        str | None
    notes:        list[str]
    stars_legend: str
```

This decoupling means renderers are pure functions: `SummaryTable → str | bytes`.
Adding a new renderer (Markdown, Excel, Quarto) requires touching exactly one file.

### `TableRow`

```python
@dataclass
class TableRow:
    label:        str        # left column text
    values:       list[str]  # one pre-formatted string per model
    is_stat:      bool       # SE / t-stat row — rendered smaller
    is_separator: bool       # horizontal rule
    is_gof:       bool       # goodness-of-fit section row
```

All formatting (rounding, stars, brackets) happens in `_summary.py` before
the row is constructed. Renderers receive already-formatted strings.

---

## Adapter layer (`_adapters.py`)

### Dispatch

`tidy(model)` and `glance(model)` use lazy-import isinstance checks:

```python
def _dispatch_tidy(model):
    if _is_statsmodels(model): return _tidy_statsmodels
    if _is_pyfixest(model):    return _tidy_pyfixest
    if _is_linearmodels(model):return _tidy_linearmodels
    raise TypeError(...)
```

Each guard (`_is_statsmodels`, etc.) wraps the import in a try/except so
missing optional dependencies only raise when that backend is actually used.

### Adding a backend

1. Add a `_is_<backend>` guard.
2. Write `_tidy_<backend>(model, conf_level) -> pd.DataFrame`.
3. Write `_glance_<backend>(model) -> pd.DataFrame`.
4. Register both in `_dispatch_tidy` and `_dispatch_glance`.
5. The schema validators (`_validate_tidy`, `_validate_glance`) will enforce
   correctness automatically — missing columns become NaN, extras are dropped.

---

## Summary builder (`_summary.py`)

`modelsummary()` proceeds in five steps:

1. **Normalise input** — `list[model]` → `dict[label, model]`
2. **Extract** — call `tidy()` and `glance()` for every model
3. **Build coefficient rows** — ordered union of terms, with estimate + stat sub-rows
4. **Build GOF rows** — from `glance()` output, filtered by `gof_map`
5. **Dispatch to renderer** — inferred from `output` extension or keyword

All cell formatting (rounding via `fmt`, star appending, stat brackets) is
applied in step 3 before `TableRow` construction. Renderers never format numbers.

---

## Renderers

Each renderer is a pure function `render_*(table: SummaryTable) -> str | bytes`.

| Renderer | Output | Notes |
|---|---|---|
| `html.py` | `str` | Inline `<style>` tag, no external CSS |
| `latex.py` | `str` | Requires `\usepackage{booktabs}` |
| `docx.py` | `bytes` | Times New Roman, three-border style |

File output is handled in `_summary.py::_render()` — renderers themselves
return strings/bytes and never touch the filesystem.

---

## Validation layer (`validate/`)

### `fixtures.py`

Contains `ModelFixture` dataclasses with:
- `model_factory` — a string of Python code that is `exec()`'d to produce `model`
- `coefs` — list of `CoefFixture` with expected values from R or Stata
- `tol_coef`, `tol_se` — per-fixture tolerances

This design means fixtures are self-contained and runnable without any
external data files. All required data is embedded inline in the factory string.

### `runner.py`

1. `exec()` each fixture's `model_factory`
2. Call `tidy()` on the resulting model
3. Compare each term's `estimate`, `std_error`, `statistic` to the expected values
4. Report pass/fail with Δ (absolute difference) shown for failures

The CLI entry point (`tidyecon-validate`) exits with code 0 on full pass,
code 1 on any failure — suitable for CI use.
