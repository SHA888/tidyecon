"""
tests/test_summary.py
=====================
Tests for modelsummary() — structure, content, and all three renderers.
"""

import tidyecon as te

# Fixtures: mtcars, models injected from conftest.py


# ── HTML output ───────────────────────────────────────────────────────────────


class TestHTMLOutput:
    def test_returns_string(self, models):
        out = te.modelsummary(models, output="html")
        assert isinstance(out, str)

    def test_contains_table_tag(self, models):
        out = te.modelsummary(models, output="html")
        assert "<table" in out

    def test_col_labels_present(self, models):
        out = te.modelsummary(models, output="html")
        for label in models:
            assert label in out

    def test_coefficient_names_present(self, models):
        out = te.modelsummary(models, output="html")
        assert "hp" in out
        assert "wt" in out

    def test_stars_present_by_default(self, models):
        out = te.modelsummary(models, output="html")
        assert "***" in out or "**" in out or "*" in out

    def test_no_stars_when_disabled(self, models):
        out = te.modelsummary(models, stars=False, output="html")
        assert "***" not in out

    def test_nobs_in_table(self, models):
        out = te.modelsummary(models, output="html")
        assert "32" in out  # mtcars has 32 rows

    def test_title_in_output(self, models):
        out = te.modelsummary(models, title="My Table", output="html")
        assert "My Table" in out

    def test_notes_in_output(self, models):
        out = te.modelsummary(models, notes=["Source: mtcars"], output="html")
        assert "Source: mtcars" in out

    def test_coef_map_renames(self, models):
        out = te.modelsummary(
            models,
            coef_map={"hp": "Horsepower", "wt": "Weight", "const": "Intercept"},
            output="html",
        )
        assert "Horsepower" in out
        assert "hp" not in out.replace("Horsepower", "")  # original name gone

    def test_coef_omit_removes_term(self, models):
        out = te.modelsummary(models, coef_omit=["const"], output="html")
        # intercept row should be gone
        assert "const" not in out

    def test_statistic_tstat(self, models):
        out = te.modelsummary(models, statistic="tstat", output="html")
        assert "[" in out  # tstat cells are formatted as [value]

    def test_list_input(self, models):
        model_list = list(models.values())
        out = te.modelsummary(model_list, output="html")
        assert "(1)" in out
        assert "(2)" in out


# ── LaTeX output ──────────────────────────────────────────────────────────────


class TestLaTeXOutput:
    def test_returns_string(self, models):
        out = te.modelsummary(models, output="latex")
        assert isinstance(out, str)

    def test_contains_tabular(self, models):
        out = te.modelsummary(models, output="latex")
        assert "\\begin{tabular}" in out

    def test_contains_toprule(self, models):
        out = te.modelsummary(models, output="latex")
        assert "\\toprule" in out

    def test_contains_bottomrule(self, models):
        out = te.modelsummary(models, output="latex")
        assert "\\bottomrule" in out

    def test_coefficient_names_present(self, models):
        out = te.modelsummary(models, output="latex")
        assert "hp" in out


# ── Word / docx output ────────────────────────────────────────────────────────


class TestDocxOutput:
    def test_returns_bytes(self, models):
        out = te.modelsummary(models, output="docx")
        assert isinstance(out, bytes)

    def test_bytes_is_valid_docx_magic(self, models):
        out = te.modelsummary(models, output="docx")
        # .docx files are zip archives — start with PK magic bytes
        assert out[:2] == b"PK"

    def test_write_to_file(self, models, tmp_path):
        p = tmp_path / "table.docx"
        result = te.modelsummary(models, output=str(p))
        assert result == p
        assert p.exists()
        assert p.stat().st_size > 1000


# ── File output ───────────────────────────────────────────────────────────────


class TestFileOutput:
    def test_html_to_file(self, models, tmp_path):
        p = tmp_path / "table.html"
        result = te.modelsummary(models, output=str(p))
        assert result == p
        assert p.read_text(encoding="utf-8").startswith("<div")

    def test_latex_to_file(self, models, tmp_path):
        p = tmp_path / "table.tex"
        result = te.modelsummary(models, output=str(p))
        assert result == p
        assert "\\begin{table}" in p.read_text(encoding="utf-8")
