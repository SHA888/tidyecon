"""
renderers/latex.py
==================
Renders a SummaryTable to a LaTeX string.

Requires in the document preamble:
    \\usepackage{booktabs}
    \\usepackage{siunitx}   % optional — for column alignment

Output is a floating `table` environment with a `tabular` inside.
"""

from __future__ import annotations

from .._protocol import SummaryTable

_PREAMBLE_NOTE = "% Requires \\usepackage{booktabs} in preamble\n"


def render_latex(table: SummaryTable) -> str:
    n_cols = len(table.col_labels)
    # Column spec: label (left) + n_cols centred data columns
    col_spec = "l" + "c" * n_cols

    lines: list[str] = [_PREAMBLE_NOTE]
    lines.append("\\begin{table}[htbp]")
    lines.append("  \\centering")

    if table.title:
        lines.append(f"  \\caption{{{_tex(table.title)}}}")

    lines.append(f"  \\begin{{tabular}}{{{col_spec}}}")
    lines.append("    \\toprule")

    # Header row
    header_cells = [""] + [_tex(c) for c in table.col_labels]
    lines.append("    " + " & ".join(header_cells) + " \\\\")
    lines.append("    \\midrule")

    # Body
    for row in table.rows:
        if row.is_separator:
            lines.append("    \\midrule")
            continue
        cells = [_tex(row.label)] + [_tex(v) for v in row.values]
        suffix = " \\\\"
        if row.is_stat:
            # stat rows: smaller font, no extra spacing after
            line = "    \\small " + " & ".join(cells) + suffix
        else:
            line = "    " + " & ".join(cells) + suffix
        lines.append(line)

    lines.append("    \\bottomrule")
    lines.append("  \\end{tabular}")

    # Notes
    note_parts = []
    if table.stars_legend:
        note_parts.append(table.stars_legend)
    note_parts.extend(table.notes)
    if note_parts:
        lines.append("  \\begin{tablenotes}[flushleft]")
        for note in note_parts:
            lines.append(f"    \\small \\item {_tex(note)}")
        lines.append("  \\end{tablenotes}")
        # Alternative without threeparttable:
        # for note in note_parts:
        #     lines.append(f"  {{\\footnotesize {_tex(note)}}}")

    lines.append("\\end{table}")
    return "\n".join(lines)


def _tex(s: str) -> str:
    """Escape characters that are special in LaTeX."""
    if not s:
        return s
    replacements = {
        "&": "\\&",
        "%": "\\%",
        "$": "\\$",
        "#": "\\#",
        "_": "\\_",
        "{": "\\{",
        "}": "\\}",
        "~": "\\textasciitilde{}",
        "^": "\\textasciicircum{}",
        "\\": "\\textbackslash{}",
        "²": "$^{2}$",  # R²
    }
    result = ""
    for ch in s:
        result += replacements.get(ch, ch)
    # Stars are safe in LaTeX math mode; keep as-is
    return result
