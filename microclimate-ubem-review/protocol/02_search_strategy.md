# Search Strategy

Each search must be logged with date, query string, source, raw output path,
normalized output path, returned count, and notes. The canonical term groups
are implemented in `scripts/search_terms.py`.

## Term Groups

### Group A: UBEM Core

```text
"urban building energy modeling"
"urban building energy modelling"
"UBEM"
"city-scale building energy simulation"
"district-scale building energy modeling"
"building stock energy modeling"
```

### Group B: Microclimate Core

```text
"urban microclimate"
"urban heat island"
"local climate"
"urban climate"
"urban canopy model"
"microclimate data"
```

### Group C: Coupling

```text
"coupling"
"co-simulation"
"integrated model"
"weather file transformation"
"urban weather generator"
"WRF"
"ENVI-met"
"CFD"
"UCM"
```

### Group D: Evaluation

```text
"uncertainty"
"validation"
"calibration"
"sensitivity analysis"
"energy demand"
"cooling demand"
"heating demand"
"overheating"
"thermal comfort"
```

## Combination Rule

Search strings must combine UBEM terms with microclimate, urban climate,
coupling, validation, uncertainty, and energy performance terms. The default
API-friendly query generator uses:

```text
Group A + Group B + one Group C term
Group A + Group B + one Group D term
```

For databases that support Boolean search, use the compact Boolean expression:

```powershell
python scripts/search_terms.py --format boolean
```

For APIs or search forms that work better with plain text queries, generate a
bounded query list:

```powershell
python scripts/search_terms.py --format simple --limit 60
```

## Search Sources

- OpenAlex API
- Crossref API
- arXiv API
- Local BibTeX exports in `data/raw/bibtex/`
- Local CSV exports in `data/raw/csv/`

## Logging Rule

Every import or API search must append a row to `logs/search_log.csv` with:

- `searched_at`
- `source`
- `query`
- `raw_output`
- `normalized_output`
- `records_returned`
- `notes`

## Data Storage Rule

- Raw API JSONL outputs go under `data/raw/api/`.
- Raw database CSV exports go under `data/raw/csv/`.
- Raw BibTeX exports go under `data/raw/bibtex/`.
- Normalized records go to `data/processed/all_records.csv`.
- Deduplicated records go to `data/processed/deduplicated_records.csv`.
- PRISMA-style counts go to `data/processed/prisma_counts.csv`.

## Deduplication Rule

Deduplicate by normalized DOI first. For records without matching DOI, use
normalized title similarity with a default threshold of `0.92`. Record the
deduplication method and match score in the deduplicated table.
