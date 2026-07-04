"""Build and validate the evidence matrix for microclimate-aware UBEM.

The script copies bibliographic metadata and screening decisions only. Evidence
fields are initialized as `not reported`; do not infer paper findings from
metadata.
"""

from __future__ import annotations

import argparse
import collections
import sys
from pathlib import Path

from review_schema import (
    EVIDENCE_COLUMNS,
    MISSINGNESS_COLUMNS,
    VALIDATION_REPORT_COLUMNS,
    read_csv,
    write_csv,
)


NOT_REPORTED = "not reported"

CATEGORICAL_ALLOWED = {
    "study_type": {
        "empirical",
        "modeling",
        "review",
        "methodological",
        "framework",
        "case_study",
        "dataset",
        NOT_REPORTED,
    },
    "review_or_original": {"review", "original", NOT_REPORTED},
    "spatial_scale": {
        "neighborhood",
        "campus",
        "district",
        "city",
        "regional",
        "stock",
        "multi-city",
        NOT_REPORTED,
    },
    "coupling_direction": {"one-way", "two-way", "offline", "online", "iterative", NOT_REPORTED},
    "temporal_resolution": {"sub-hourly", "hourly", "daily", "monthly", "annual", "scenario", NOT_REPORTED},
    "reproducibility": {"code/data available", "partial", "unavailable", NOT_REPORTED},
    "relevance_to_review": {"high", "medium", "low", "background", NOT_REPORTED},
}

SUMMARY_FIELDS = [
    "microclimate_data_source",
    "coupling_strategy",
    "validation_data",
    "uncertainty_method",
    "reported_energy_impact",
    "policy_application",
]


def selected_screening(rows: list[dict[str, str]], include_excluded: bool) -> list[dict[str, str]]:
    allowed = {"include", "uncertain"}
    if include_excluded:
        allowed.add("exclude")
    selected = []
    for row in rows:
        decision = (row.get("screening_decision") or "").strip().lower()
        if decision in allowed:
            selected.append(row)
    return selected


def index_records(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row.get("paper_id", ""): row for row in rows if row.get("paper_id")}


def empty_evidence_row() -> dict[str, str]:
    return {field: NOT_REPORTED for field in EVIDENCE_COLUMNS}


def build_matrix(records: dict[str, dict[str, str]], screening: list[dict[str, str]]) -> list[dict[str, str]]:
    matrix = []
    for screen in screening:
        record = records.get(screen.get("paper_id", ""), {})
        row = empty_evidence_row()
        doi = record.get("DOI") or screen.get("DOI", "")
        row.update(
            {
                "paper_id": screen.get("paper_id", ""),
                "citation_key": record.get("citation_key") or screen.get("citation_key", ""),
                "title": record.get("title") or screen.get("title", ""),
                "year": record.get("year") or screen.get("year", ""),
                "source": record.get("source") or screen.get("source", ""),
                "DOI": doi,
                "journal": record.get("venue", ""),
                "doi": doi,
                "relevance_to_review": (
                    "not reported"
                    if screen.get("screening_decision") == "uncertain"
                    else "medium"
                ),
            }
        )
        matrix.append(row)
    return matrix


def is_missing(value: str) -> bool:
    return value.strip() == "" or value.strip().lower() == NOT_REPORTED


def missingness(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    total = len(rows)
    report = []
    for field in EVIDENCE_COLUMNS:
        missing_count = sum(1 for row in rows if is_missing(row.get(field, "")))
        percent = (missing_count / total * 100) if total else 0.0
        report.append(
            {
                "field": field,
                "missing_count": str(missing_count),
                "total_count": str(total),
                "missing_percent": f"{percent:.1f}",
            }
        )
    return report


def validate_categorical(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    issues = []
    for row in rows:
        for field, allowed in CATEGORICAL_ALLOWED.items():
            value = row.get(field, "").strip()
            if not value:
                continue
            parts = [part.strip().lower() for part in value.split(";") if part.strip()]
            invalid = [part for part in parts if part not in allowed]
            for part in invalid:
                issues.append(
                    {
                        "paper_id": row.get("paper_id", ""),
                        "field": field,
                        "value": part,
                        "issue": "Value is outside the codebook category set.",
                    }
                )
    return issues


def count_field(rows: list[dict[str, str]], field: str) -> list[dict[str, str]]:
    counter: collections.Counter[str] = collections.Counter()
    for row in rows:
        value = row.get(field, "").strip() or NOT_REPORTED
        for part in [part.strip() for part in value.split(";") if part.strip()]:
            counter[part] += 1
    return [{"value": value, "count": str(count)} for value, count in counter.most_common()]


def export_summary_tables(rows: list[dict[str, str]], tables_dir: Path) -> None:
    tables_dir.mkdir(parents=True, exist_ok=True)
    for field in SUMMARY_FIELDS:
        write_csv(tables_dir / f"summary_{field}.csv", count_field(rows, field), ["value", "count"])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", default="data/processed/deduplicated_records.csv")
    parser.add_argument("--screening", default="data/processed/screening_results.csv")
    parser.add_argument("--output", default="data/processed/evidence_matrix.csv")
    parser.add_argument("--missingness-output", default="data/processed/evidence_missingness_report.csv")
    parser.add_argument("--validation-output", default="data/processed/evidence_validation_report.csv")
    parser.add_argument("--tables-dir", default="manuscript/tables")
    parser.add_argument("--include-excluded", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    records_path = Path(args.records)
    screening_path = Path(args.screening)
    if not records_path.exists():
        print(f"Records file not found: {records_path}", file=sys.stderr)
        return 1
    if not screening_path.exists():
        print(f"Screening file not found: {screening_path}", file=sys.stderr)
        return 1

    records = index_records(read_csv(records_path))
    screening = selected_screening(read_csv(screening_path), args.include_excluded)
    matrix = build_matrix(records, screening)

    write_csv(Path(args.output), matrix, EVIDENCE_COLUMNS)
    write_csv(Path(args.missingness_output), missingness(matrix), MISSINGNESS_COLUMNS)
    write_csv(Path(args.validation_output), validate_categorical(matrix), VALIDATION_REPORT_COLUMNS)
    export_summary_tables(matrix, Path(args.tables_dir))

    print(f"Wrote {len(matrix)} evidence matrix rows")
    print(f"Wrote missingness report to {args.missingness_output}")
    print(f"Wrote validation report to {args.validation_output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
