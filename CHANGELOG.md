# Changelog

All notable changes to tidyecon are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Added
- `tidy()` — unified coefficient table for statsmodels, pyfixest, linearmodels
- `glance()` — unified model statistics
- `modelsummary()` — publication tables to HTML, LaTeX, and Word
- `tidyecon-validate` CLI — numerical benchmark suite against R 4.4.1
- Validation fixtures: OLS and Logit on mtcars (R broom reference values)
- 43 tests covering all three renderers and both adapters

### Known gaps (targeted for v0.1.0)
- pyfixest and linearmodels: schema-validated but no numerical fixtures yet
- LaTeX: `threeparttable` wrapping for notes not yet implemented
- docx: multi-line notes collapse to one row

---

## [0.1.0] — TBD

First public release. See TODO.md for release checklist.
