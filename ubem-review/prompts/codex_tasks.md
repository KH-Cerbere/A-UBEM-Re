# Codex Tasks for the UBEM Review

Use these prompts to keep research assistance auditable.

## Import and Cleaning

```text
Inspect data/raw_bib and summarize which files are present. Do not infer or
invent missing bibliographic fields. Then run the import and deduplication
scripts and report how many records were produced.
```

## Screening Support

```text
Given the screening CSV and imported records, identify records marked maybe and
summarize only the title, abstract, and existing metadata. Do not make claims
that are not supported by those fields.
```

## Evidence Extraction

```text
For records marked include, prepare an extraction checklist with fields for
scale, data sources, simulation engine, calibration, validation, uncertainty,
and application domain. Leave fields blank when the source does not state them.
```

## Manuscript Drafting

```text
Draft text only from the evidence matrix and annotated bibliography. Cite source
record IDs for every substantive claim. Do not add papers, DOI values, or
publisher details that are absent from the data.
```
