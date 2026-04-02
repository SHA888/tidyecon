"""
_summary.py
===========
modelsummary() — one-function publication tables.

Mirrors the API of R's modelsummary package as closely as Python allows.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Literal

import numpy as np
import pandas as pd

from ._adapters import glance, tidy
from ._protocol import DEFAULT_STARS, SummaryTable, TableRow, _stars

# ── Default GOF rows (order matters — this is the display order) ──────────────
DEFAULT_GOF: list[tuple[str, str]] = [
    ("nobs", "N"),
    ("r_squared", "R²"),
    ("adj_r_squared", "Adj. R²"),
    ("rmse", "RMSE"),
    ("f_statistic", "F"),
    ("fixed_effects", "Fixed effects"),
    ("vcov_type", "Std. errors"),
]

_FMT_INT = "{:.0f}"
_FMT_FLOAT = "{:.3f}"


# ── Public API ────────────────────────────────────────────────────────────────


def modelsummary(
    models: dict[str, Any] | list[Any],
    *,
    stars: bool | dict[str, float] = True,
    statistic: Literal["se", "tstat", "pvalue", "confint"] = "se",
    fmt: str = "{:.3f}",
    coef_map: dict[str, str] | None = None,
    coef_omit: list[str] | None = None,
    gof_map: list[str] | None = None,
    title: str | None = None,
    notes: list[str] | None = None,
    output: str = "html",
) -> str | Path | None:
    """
    Produce a publication-ready regression table.

    Parameters
    ----------
    models : dict {label: model} or list of models (auto-labelled (1),(2),…)
    stars  : True for defaults, False for none, or dict {"***": 0.01, ...}
    statistic : what to show under estimates — "se", "tstat", "pvalue", "confint"
    fmt    : Python format string for numeric cells, e.g. "{:.3f}"
    coef_map : rename / reorder coefficients {old_name: new_name}
    coef_omit : list of term patterns (regex) to drop
    gof_map : which glance columns to include, in order
    title : table caption
    notes : footnote lines appended below the table
    output : "html" | "latex" | "docx" | path ending in .html/.tex/.docx

    Returns
    -------
    str   (HTML or LaTeX),
    Path  (docx written to disk),
    or None (HTML/LaTeX written to disk)
    """
    # ── Normalise models input ─────────────────────────────────────────────
    if isinstance(models, list):
        named = {f"({i + 1})": m for i, m in enumerate(models)}
    else:
        named = dict(models)

    star_thresholds: dict[str, float] | None = (
        DEFAULT_STARS if stars is True else None if stars is False else stars
    )

    # ── Extract tidy + glance for each model ──────────────────────────────
    tidy_frames = {k: tidy(m) for k, m in named.items()}
    glance_frames = {k: glance(m) for k, m in named.items()}

    # ── Build coefficient grid ─────────────────────────────────────────────
    table = _build_summary_table(
        col_labels=list(named.keys()),
        tidy_frames=tidy_frames,
        glance_frames=glance_frames,
        statistic=statistic,
        fmt=fmt,
        star_thresholds=star_thresholds,
        coef_map=coef_map,
        coef_omit=coef_omit,
        gof_map=gof_map,
        title=title,
        notes=notes or [],
    )

    # ── Dispatch to renderer ───────────────────────────────────────────────
    return _render(table, output)


# ── Table builder ─────────────────────────────────────────────────────────────


def _build_summary_table(
    col_labels: list[str],
    tidy_frames: dict[str, pd.DataFrame],
    glance_frames: dict[str, pd.DataFrame],
    statistic: str,
    fmt: str,
    star_thresholds: dict[str, float] | None,
    coef_map: dict[str, str] | None,
    coef_omit: list[str] | None,
    gof_map: list[str] | None,
    title: str | None,
    notes: list[str],
) -> SummaryTable:
    # 1. Collect ordered union of terms
    all_terms: list[str] = []
    seen: set[str] = set()
    for df in tidy_frames.values():
        for t in df["term"]:
            if t not in seen:
                all_terms.append(t)
                seen.add(t)

    # 2. Apply coef_omit (regex patterns)
    if coef_omit:
        pattern = "|".join(coef_omit)
        all_terms = [t for t in all_terms if not re.search(pattern, t)]

    # 3. Apply coef_map (rename + filter + reorder)
    if coef_map:
        all_terms = [t for t in all_terms if t in coef_map]
        display_names = {t: coef_map[t] for t in all_terms}
    else:
        display_names = {t: t for t in all_terms}

    # 4. Build coefficient rows (estimate row + statistic row per term)
    coef_rows: list[TableRow] = []
    for term in all_terms:
        est_cells = []
        stat_cells = []
        for col in col_labels:
            df = tidy_frames[col]
            row = df[df["term"] == term]
            if row.empty:
                est_cells.append("")
                stat_cells.append("")
            else:
                r = row.iloc[0]
                star_str = _stars(r["p_value"], star_thresholds) if star_thresholds else ""
                est_cells.append(fmt.format(r["estimate"]) + star_str)
                stat_cells.append(_stat_cell(r, statistic, fmt))

        coef_rows.append(TableRow(label=display_names[term], values=est_cells))
        coef_rows.append(TableRow(label="", values=stat_cells, is_stat=True))

    # 5. Build GOF rows
    effective_gof = gof_map if gof_map else [k for k, _ in DEFAULT_GOF]
    gof_labels = dict(DEFAULT_GOF)

    gof_rows: list[TableRow] = []
    for col_key in effective_gof:
        label = gof_labels.get(col_key, col_key)
        cells = []
        for col in col_labels:
            gdf = glance_frames[col]
            if col_key not in gdf.columns:
                cells.append("")
                continue
            val = gdf.iloc[0][col_key]
            cells.append(_fmt_gof(val, col_key, fmt))
        if any(c for c in cells):
            gof_rows.append(TableRow(label=label, values=cells, is_gof=True))

    # 6. Assemble
    rows: list[TableRow] = (
        coef_rows
        + [TableRow(label="", values=[""] * len(col_labels), is_separator=True)]
        + gof_rows
    )

    legend = "* p<0.1  ** p<0.05  *** p<0.01" if star_thresholds else ""

    return SummaryTable(
        col_labels=col_labels,
        rows=rows,
        title=title,
        notes=notes,
        stars_legend=legend,
    )


def _stat_cell(row: pd.Series, statistic: str, fmt: str) -> str:
    if statistic == "se":
        v = row["std_error"]
        return f"({fmt.format(v)})" if not np.isnan(v) else ""
    if statistic == "tstat":
        v = row["statistic"]
        return f"[{fmt.format(v)}]" if not np.isnan(v) else ""
    if statistic == "pvalue":
        v = row["p_value"]
        return f"({fmt.format(v)})" if not np.isnan(v) else ""
    if statistic == "confint":
        lo, hi = row["conf_low"], row["conf_high"]
        if np.isnan(lo) or np.isnan(hi):
            return ""
        return f"[{fmt.format(lo)}, {fmt.format(hi)}]"
    return ""


def _fmt_gof(val: Any, key: str, fmt: str) -> str:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return ""
    if isinstance(val, str):
        return val
    if key == "nobs":
        return f"{int(val):,}"
    try:
        return fmt.format(float(val))
    except (TypeError, ValueError):
        return str(val)


# ── Renderer dispatch ──────────────────────────────────────────────────────────


def _render(table: SummaryTable, output: str) -> str | Path | None:
    from .renderers.docx import render_docx
    from .renderers.html import render_html
    from .renderers.latex import render_latex

    out = output.strip()
    ext = Path(out).suffix.lower() if out not in ("html", "latex", "docx") else f".{out}"

    if ext in (".html", ".htm") or out == "html":
        result = render_html(table)
        if out == "html":
            return result
        p = Path(out)
        p.write_text(result, encoding="utf-8")
        return p

    if ext in (".tex", ".latex") or out == "latex":
        result = render_latex(table)
        if out == "latex":
            return result
        p = Path(out)
        p.write_text(result, encoding="utf-8")
        return p

    if ext == ".docx" or out == "docx":
        buf = render_docx(table)
        if out == "docx":
            return buf  # bytes
        p = Path(out)
        p.write_bytes(buf)
        return p

    raise ValueError(
        f"Unknown output format: {output!r}. "
        "Use 'html', 'latex', 'docx', or a file path ending in .html/.tex/.docx"
    )
