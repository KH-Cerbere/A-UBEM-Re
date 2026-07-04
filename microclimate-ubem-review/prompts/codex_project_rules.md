# Codex Project Rules

- Treat this as a research repository, not a manuscript generator.
- Preserve source traceability from raw records to processed tables and notes.
- Do not invent citations, DOI values, metadata, findings, or numerical results.
- Codex must never infer paper content that is not present in the provided
  abstract, PDF note, or extraction table.
- Every output table must preserve `paper_id`, `title`, `year`, `source`,
  `DOI`, and `citation_key`.
- Do not write narrative claims unless they are backed by records in the
  evidence matrix or annotated bibliography.
- Prefer small, auditable script changes over manual spreadsheet edits.
- Log important search, screening, extraction, and code changes.
- Keep automated screening labels separate from human reviewer decisions.
- When screening is uncertain, mark `uncertain` rather than forcing an include
  or exclude decision.
- For screening, use `uncertain` rather than `exclude` when metadata is
  insufficient.
- In the evidence matrix, write `not reported` for absent information.
