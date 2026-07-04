# Extraction Prompts

Use these prompts only with source text or notes that are linked to a
`paper_id`.

## Evidence Extraction

For paper `{paper_id}`, extract only information explicitly supported by the
provided source text. Fill the evidence matrix fields listed in
`protocol/05_data_extraction_codebook.md`. If a field is not reported, write
`not reported`. Do not infer methods, tools, validation, or impacts that are not
visible in the source.

Prioritize these synthesis-critical fields:

- `microclimate_data_source`
- `coupling_strategy`
- `validation_data`
- `uncertainty_method`
- `reported_energy_impact`
- `policy_application`

## Consistency Check

Compare the extracted fields for `{paper_id}` against the codebook. Identify
fields that are unsupported, ambiguous, or need full-text verification. Do not
rewrite the paper note into manuscript prose.
