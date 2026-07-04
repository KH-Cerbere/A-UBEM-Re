# Screening Protocol

## Screening Stages

1. Import raw records from APIs or database exports.
2. Normalize records into `data/processed/all_records.csv`.
3. Deduplicate records into `data/processed/deduplicated_records.csv`.
4. Apply the criteria in `protocol/03_inclusion_exclusion_criteria.md`.
5. Write screening decisions to `data/processed/screening_results.csv`.
6. Retain all `include` and `uncertain` records for evidence-matrix setup and
   manual full-text review.

## Required Screening Fields

- `paper_id`
- `title`
- `year`
- `source`
- `DOI`
- `citation_key`
- `abstract_available`
- `screening_decision`: include, exclude, or uncertain
- `reason`
- `confidence`: high, medium, or low
- `matched_terms`

## Rules

- Do not exclude a paper solely because the abstract is missing.
- If the paper mentions UBEM and microclimate but the energy outcome is unclear,
  mark `uncertain`.
- If the paper is a general UBEM review but has no visible microclimate
  relevance, mark `exclude` unless a human reviewer retains it as background.
- Keep all uncertain records for manual review.
- Do not infer paper content beyond title, abstract, keywords, venue, and other
  local metadata.

## Example Reasons

- `Matches UBEM, microclimate, energy/performance outcome, and urban-scale criteria.`
- `Mentions UBEM and microclimate, but energy/performance outcome is unclear.`
- `Abstract missing and metadata is insufficient for reliable screening.`
- `Microclimate or urban-climate signal is visible, but no building-energy outcome is visible.`
- `UBEM/building-energy signal is visible, but no microclimate relevance is visible in metadata.`
