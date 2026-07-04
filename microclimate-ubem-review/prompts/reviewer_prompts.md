# Reviewer Prompts

## Title/Abstract Screening

Given the title, abstract, venue, and keywords for `{paper_id}`, decide whether
the record should be `include`, `exclude`, or `uncertain` under
`protocol/03_inclusion_exclusion_criteria.md`. Provide one short reason.
Do not exclude a paper solely because the abstract is missing.

## Full-Text Eligibility

Given source text or detailed notes for `{paper_id}`, decide whether both sides
of the review scope are present:

- urban-scale, district-scale, city-scale, or stock-scale building energy
  modeling;
- microclimate, urban climate, weather adjustment, urban canopy, heat island, or
  related local climate representation.

Return the decision, reason, and any extraction fields that need follow-up.
Keep `uncertain` records for manual review.

## Synthesis Guardrail

List claims that are supported by at least two extracted records. For each
claim, cite the supporting `paper_id` values. Do not include unsupported
generalizations.
