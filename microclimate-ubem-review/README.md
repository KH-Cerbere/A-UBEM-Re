# Microclimate-UBEM Review

This repository is a reproducible research workspace for a literature review on
how urban microclimate information is represented, coupled, validated, and used
in Urban Building Energy Modeling (UBEM) and related city-scale building energy
simulation.

This is a research repository first. Manuscript files are placeholders until
the search, screening, extraction, and synthesis workflow has produced auditable
evidence.

## Research Scope

The review focuses on studies that connect urban microclimate, urban canopy,
weather morphing, local climate zones, street-canyon effects, heat island
effects, or mesoscale/microscale climate models with building energy demand at
district, neighborhood, city, stock, or urban scale.

## Non-Negotiable Rules

- Do not invent papers, authors, journals, DOI values, years, abstracts, or
  findings.
- Do not fill missing metadata by guessing.
- All scripts must read from local data files or documented public APIs.
- Every output table must preserve these identity columns: `paper_id`, `title`,
  `year`, `source`, `DOI`, and `citation_key`.
- Codex must never infer paper content that is not present in the provided
  abstract, PDF note, or extraction table.
- Preserve raw search exports and API responses under `data/raw/`.
- Keep processed tables under `data/processed/`.
- Record each search, screening, extraction, and code change in `logs/`.
- Treat automated title/abstract screening as a candidate label only. Human
  review decisions must be recorded separately.
- Do not write manuscript argumentation before evidence extraction and synthesis
  tables exist.

## Repository Layout

```text
protocol/                  Review protocol, search strategy, criteria, codebook
data/raw/bibtex/           Local BibTeX exports
data/raw/csv/              Raw CSV exports from databases
data/raw/api/              Raw API JSONL responses
data/raw/pdf_metadata/     PDF metadata or full-text inventory exports
data/processed/            Normalized records, screening results, evidence matrix
scripts/                   Reproducible fetch, clean, screen, analyze, plot scripts
literature/paper_notes/    One note per paper after import and screening
literature/                Annotated bibliography and key-paper register
manuscript/                Outline and section placeholders only in Phase 1
prompts/                   Codex and reviewer prompts used during the review
logs/                      Screening and Codex change logs
```

## Phase 1 Workflow

1. Define the review position and questions in `protocol/`.
2. Run database/API searches with exact query, date, source, and filters logged.
3. Save raw results under `data/raw/`.
4. Normalize records into `data/processed/all_records.csv` with the required
   identity columns.
5. Deduplicate into `data/processed/deduplicated_records.csv` and assign stable
   `paper_id` values.
6. Create title/abstract screening candidates in
   `data/processed/screening_results.csv`.
7. Fill human reviewer decisions and reasons.
8. Build `data/processed/evidence_matrix.csv` only for included or maybe
   records.
9. Write paper notes and annotated bibliography entries only after source
   records are traceable.

## Required Output Columns

Every paper-level output table must keep these columns, preferably first:

```text
paper_id,title,year,source,DOI,citation_key
```

If `paper_id` has not been assigned yet, the column must still exist and remain
blank until deduplication assigns a stable local ID.

## Example Commands

Run commands from the `microclimate-ubem-review/` directory.

```powershell
python scripts/fetch_openalex.py --max-results 100
python scripts/fetch_crossref.py --max-results 100
python scripts/fetch_arxiv.py --max-results 50
python scripts/clean_bibtex.py
python scripts/import_csv.py
python scripts/deduplicate_records.py
python scripts/screen_titles_abstracts.py
python scripts/build_evidence_matrix.py
python scripts/build_prisma_counts.py
python scripts/generate_framework_figure.py
python scripts/analyze_keywords.py
python scripts/plot_review_figures.py
```

The scripts use the Python standard library by default. Plotting writes CSV
outputs even when optional plotting libraries are unavailable.

## Search Pipeline

The canonical search terms live in `scripts/search_terms.py` and are grouped as
UBEM core, microclimate core, coupling, and evaluation terms. API scripts use
generated combinations by default and append every source-query-count event to
`logs/search_log.csv`.

Deduplication is DOI-first, then title-similarity based. The deduplicated table
records `dedupe_method` and `dedupe_match_score`.

## Screening and Evidence Matrix

Title/abstract screening reads `data/processed/deduplicated_records.csv` and
writes `data/processed/screening_results.csv` with `include`, `exclude`, or
`uncertain` decisions. Records marked `uncertain` are retained for manual
review.

The evidence matrix is initialized from included and uncertain records. Evidence
fields are filled with `not reported` until supported by an abstract, PDF note,
or extraction table. The build script also writes missingness and validation
reports plus summary tables for the synthesis-critical fields.

## Framework and Figures

The conceptual framework is defined in
`protocol/06_conceptual_framework.md`. Generate the framework figure with:

```powershell
python scripts/generate_framework_figure.py
```

Generate review figures from `data/processed/evidence_matrix.csv` with:

```powershell
python scripts/plot_review_figures.py
```

Figures are exported to `manuscript/figures/` as SVG and 600 dpi PNG, with
captions and missingness warnings. Empty evidence produces explicit empty
figures rather than fabricated values.
