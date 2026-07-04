# Codex Change Log

## 2026-07-04 - Repository Scaffold

- Created Phase 1 research repository structure.
- Added protocol, data, script, literature, manuscript, prompt, and log
  placeholders.
- Added standard-library Python scripts for fetching, cleaning, deduplication,
  candidate screening, evidence matrix creation, keyword analysis, and summary
  table generation.
- Left manuscript sections as placeholders only.

## 2026-07-04 - Required Review Schema

- Standardized paper-level output tables around `paper_id`, `title`, `year`,
  `source`, `DOI`, and `citation_key`.
- Added shared schema helpers in `scripts/review_schema.py`.
- Updated script stubs so outputs preserve traceability and never infer paper
  content beyond local records or documented public API responses.
- Added the project rule that Codex must never infer paper content not present
  in the provided abstract, PDF note, or extraction table.

## 2026-07-04 - Literature Search Pipeline

- Added canonical A-D search term groups and query builders in
  `scripts/search_terms.py`.
- Updated OpenAlex, Crossref, arXiv, BibTeX, and CSV import scripts to write
  normalized records and search-log rows.
- Updated deduplication to use DOI first, then title similarity with recorded
  match method and score.
- Added `scripts/build_prisma_counts.py` and `data/processed/prisma_counts.csv`.

## 2026-07-05 - Screening Rules and Evidence Matrix

- Rewrote inclusion/exclusion criteria around include, exclude, and uncertain
  decisions.
- Updated `scripts/screen_titles_abstracts.py` to apply protocol criteria to
  `data/processed/deduplicated_records.csv`.
- Rebuilt `data/processed/evidence_matrix.csv` around microclimate data
  sources, coupling strategies, validation data, uncertainty methods,
  energy-performance impacts, and policy applications.
- Updated `scripts/build_evidence_matrix.py` to initialize absent evidence as
  `not reported`, validate categorical fields, generate a missingness report,
  and export summary tables under `manuscript/tables/`.

## 2026-07-05 - Framework and Review Figures

- Added `protocol/06_conceptual_framework.md` with a four-layer
  microclimate-aware UBEM framework.
- Added `scripts/generate_framework_figure.py` to export the framework as DOT,
  Mermaid, SVG, and 600 dpi PNG.
- Rebuilt `scripts/plot_review_figures.py` to generate six review figures from
  `data/processed/evidence_matrix.csv`: PRISMA flow, annual publication trend,
  microclimate-variable/output heatmap, data-source/coupling/output flow,
  tool map, and validation/uncertainty/policy gap matrix.
- Added figure captions and missingness warnings without fabricating values.
