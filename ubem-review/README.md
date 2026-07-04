# UBEM Systematic Review

This repository supports a reproducible literature review on **Urban Building
Energy Modeling (UBEM)**, including city-scale building energy simulation,
urban energy modeling, and building stock energy modeling.

## Research Scope

The review focuses on methods, data pipelines, validation practices, software
tools, and application domains for modeling energy demand in urban building
stocks. It is designed to keep source records traceable from initial search to
screening, evidence extraction, figures, tables, and manuscript drafts.

## Reproducibility Rules

- Do not generate fake papers, fake authors, fake journals, or fake DOI values.
- Do not fill missing DOI, year, venue, or abstract fields by guessing.
- Use only records returned by OpenAlex, Crossref, arXiv, or records present in
  local BibTeX files.
- Preserve raw imported records under `data/raw_bib/`.
- Store cleaned and deduplicated records under `data/processed/`.
- Exclude records from MDPI or MPDI sources by default when source metadata
  makes that identifiable.
- Record screening and extraction decisions in CSV/Markdown files so that each
  decision can be audited.

## Repository Layout

```text
protocol/                  Review question, criteria, search strings, logs
data/raw_bib/              Raw API or BibTeX imports
data/processed/            Normalized, deduplicated, and screening-ready data
data/extraction_tables/    Evidence matrices and coded extraction tables
scripts/                   Reproducible import, cleaning, screening, plotting
literature/papers/         PDFs or links managed by the researcher
literature/notes/          Per-paper notes
literature/annotated_bibliography.md
manuscript/                Outline, LaTeX draft, figures, and tables
prompts/                   Codex task prompts and review checklists
```

## Basic Workflow

1. Define the review question and criteria in `protocol/`.
2. Run database searches using `scripts/fetch_openalex.py`,
   `scripts/fetch_crossref.py`, and `scripts/fetch_arxiv.py`.
3. Place any local BibTeX exports in `data/raw_bib/`.
4. Deduplicate imported records with `scripts/deduplicate_bib.py`.
5. Create or update title and abstract screening decisions with
   `scripts/screen_titles_abstracts.py`.
6. Build an extraction-ready evidence matrix with
   `scripts/build_evidence_matrix.py`.
7. Generate trend summaries and optional figures with `scripts/plot_trends.py`.
8. Keep narrative notes in `literature/` and manuscript drafts in
   `manuscript/`.

## Example Commands

Run from the `ubem-review/` directory:

```powershell
python scripts/fetch_openalex.py --query "urban building energy modeling" --max-results 100
python scripts/fetch_crossref.py --query "city-scale building energy simulation" --max-results 100
python scripts/fetch_arxiv.py --query "urban energy modeling" --max-results 50
python scripts/deduplicate_bib.py
python scripts/screen_titles_abstracts.py
python scripts/build_evidence_matrix.py
python scripts/plot_trends.py
```

The scripts use the Python standard library. `plot_trends.py` can also create a
PNG figure when `matplotlib` is installed; otherwise it still writes CSV trend
tables.

## Data Integrity

This repository is intentionally empty of literature records at initialization.
Records must enter through one of these routes:

- API responses saved by the fetch scripts.
- BibTeX files manually exported by the researcher into `data/raw_bib/`.

Any downstream table should cite the original `source` and `source_record_id`
fields produced by the import scripts.
