# Review Checklist

## Before Searching

- Review question is documented.
- Inclusion and exclusion criteria are documented.
- Search strings are versioned.
- Data provenance rules are understood.

## After Import

- Raw API or BibTeX files are preserved.
- No fake records or fake DOI values were added.
- MDPI/MPDI records were excluded when source metadata identified them.
- Each record has a `source` and `source_record_id` where available.

## After Screening

- Each record has one of `include`, `exclude`, `maybe`, or `duplicate`.
- Exclusion reasons are documented.
- Ambiguous records are marked `maybe`, not silently dropped.

## Before Manuscript Drafting

- Evidence matrix fields are traceable to source records.
- Claims in the manuscript can be linked to records or extracted notes.
- Figures and tables are generated from processed data, not manually invented.
