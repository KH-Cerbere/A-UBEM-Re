"""Build a PRISMA-style count table from local review workflow files."""

from __future__ import annotations

import argparse
from pathlib import Path

from review_schema import PRISMA_COLUMNS, read_csv, write_csv


def safe_read(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    return read_csv(path)


def effective_decision(row: dict[str, str]) -> str:
    return (row.get("screening_decision") or "").strip().lower()


def build_counts(
    all_records_path: Path,
    deduplicated_path: Path,
    screening_path: Path,
    evidence_path: Path,
) -> list[dict[str, str]]:
    all_records = safe_read(all_records_path)
    deduplicated = safe_read(deduplicated_path)
    screening = safe_read(screening_path)
    evidence = safe_read(evidence_path)

    excluded = sum(1 for row in screening if effective_decision(row) == "exclude")
    included = sum(1 for row in screening if effective_decision(row) == "include")
    uncertain = sum(1 for row in screening if effective_decision(row) == "uncertain")

    return [
        {
            "stage": "identified",
            "count": str(len(all_records)),
            "source_file": str(all_records_path),
            "notes": "All normalized records imported from APIs or local files.",
        },
        {
            "stage": "deduplicated",
            "count": str(len(deduplicated)),
            "source_file": str(deduplicated_path),
            "notes": "Records after DOI-first and title-similarity deduplication.",
        },
        {
            "stage": "screened",
            "count": str(len(screening)),
            "source_file": str(screening_path),
            "notes": "Records present in title/abstract screening table.",
        },
        {
            "stage": "excluded",
            "count": str(excluded),
            "source_file": str(screening_path),
            "notes": "Rows with screening_decision marked exclude.",
        },
        {
            "stage": "full-text assessed",
            "count": str(len(evidence)),
            "source_file": str(evidence_path),
            "notes": "Rows present in the evidence matrix; includes uncertain records retained for manual review.",
        },
        {
            "stage": "included",
            "count": str(included),
            "source_file": str(screening_path),
            "notes": "Rows with screening_decision marked include.",
        },
        {
            "stage": "uncertain",
            "count": str(uncertain),
            "source_file": str(screening_path),
            "notes": "Rows retained for manual review.",
        },
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all-records", default="data/processed/all_records.csv")
    parser.add_argument("--deduplicated", default="data/processed/deduplicated_records.csv")
    parser.add_argument("--screening", default="data/processed/screening_results.csv")
    parser.add_argument("--evidence", default="data/processed/evidence_matrix.csv")
    parser.add_argument("--output", default="data/processed/prisma_counts.csv")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    counts = build_counts(
        Path(args.all_records),
        Path(args.deduplicated),
        Path(args.screening),
        Path(args.evidence),
    )
    write_csv(Path(args.output), counts, PRISMA_COLUMNS)
    print(f"Wrote PRISMA-style counts to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
