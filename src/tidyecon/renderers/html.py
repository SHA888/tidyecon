"""
renderers/html.py
=================
Renders a SummaryTable to a self-contained HTML string.
Styled to match the aesthetics of R's modelsummary HTML output.
"""

from __future__ import annotations

from .._protocol import SummaryTable

_CSS = """
<style>
  .tidyecon-table {
    font-family: 'Times New Roman', Times, serif;
    font-size: 14px;
    border-collapse: collapse;
    margin: 1em auto;
    min-width: 400px;
  }
  .tidyecon-table caption {
    font-weight: bold;
    text-align: left;
    margin-bottom: 6px;
    font-size: 15px;
  }
  .tidyecon-table th {
    border-top: 2px solid #000;
    border-bottom: 1px solid #000;
    text-align: center;
    padding: 4px 14px;
    font-weight: bold;
  }
  .tidyecon-table td {
    text-align: center;
    padding: 2px 14px;
    white-space: nowrap;
  }
  .tidyecon-table td.label {
    text-align: left;
    font-style: normal;
  }
  .tidyecon-table tr.stat td {
    font-size: 12px;
    color: #444;
    padding-top: 0;
    padding-bottom: 4px;
  }
  .tidyecon-table tr.separator td {
    border-top: 1px solid #000;
    padding: 0;
    line-height: 0;
  }
  .tidyecon-table tr.gof td.label {
    font-style: normal;
  }
  .tidyecon-table tfoot {
    font-size: 11px;
    color: #555;
    border-top: 2px solid #000;
  }
  .tidyecon-table tfoot td {
    text-align: left;
    padding: 4px 4px 2px 4px;
  }
</style>
"""


def render_html(table: SummaryTable) -> str:
    n_cols = len(table.col_labels)
    total_cols = n_cols + 1  # +1 for label column

    lines: list[str] = ["<div class='tidyecon-wrap'>", _CSS, "<table class='tidyecon-table'>"]

    # Caption
    if table.title:
        lines.append(f"  <caption>{_esc(table.title)}</caption>")

    # Header
    lines.append("  <thead><tr>")
    lines.append("    <th></th>")
    for label in table.col_labels:
        lines.append(f"    <th>{_esc(label)}</th>")
    lines.append("  </tr></thead>")

    # Body
    lines.append("  <tbody>")
    for row in table.rows:
        if row.is_separator:
            lines.append(f"    <tr class='separator'><td colspan='{total_cols}'></td></tr>")
            continue
        css = " class='stat'" if row.is_stat else (" class='gof'" if row.is_gof else "")
        lines.append(f"    <tr{css}>")
        lines.append(f"      <td class='label'>{_esc(row.label)}</td>")
        for val in row.values:
            lines.append(f"      <td>{_esc(val)}</td>")
        lines.append("    </tr>")
    lines.append("  </tbody>")

    # Footer
    footer_items = []
    if table.stars_legend:
        footer_items.append(table.stars_legend)
    footer_items.extend(table.notes)

    if footer_items:
        lines.append("  <tfoot>")
        for item in footer_items:
            lines.append(f"    <tr><td colspan='{total_cols}'>{_esc(item)}</td></tr>")
        lines.append("  </tfoot>")

    lines.append("</table>")
    lines.append("</div>")
    return "\n".join(lines)


def _esc(s: str) -> str:
    """Minimal HTML escaping — preserves stars (*, **) and brackets."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
