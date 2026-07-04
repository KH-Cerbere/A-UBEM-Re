"""Build an extraction-ready evidence matrix from screened records.

The script copies bibliographic metadata and leaves analytical extraction fields
blank. Researchers should fill blanks only from source text or notes.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any


EXTRACTION_FIELDS = [
    "urban_scale",
    "building_stock_representation",
    "energy_end_uses",
    "simulation_engine_or_tool",
    "input_data_sources",
    "weather_or_climate_data",
    "occupancy_modeling",
    "calibration",
    "validation",
    "uncertainty_analysis",
    "application_domain",
    "key_findings",
    "limitations",
    "extraction_notes",
]


def read_jsonl(path: Path) -> dict[str, dict[str, Any]]:
    records = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            key = row.get("dedupe_key") or row.get("source_record_id") or row.get("doi")
            if key:
                records[key] = row
    return records


def read_screening(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def selected_rows(screening_rows: list[dict[str, str]], include_maybe: bool) -> list[dict[str, str]]:
    selected = []
    allowed = {"include"}
    if include_maybe:
        allowed.add("maybe")
    for row in screening_rows:
        decision = (row.get("reviewer_decision") or row.get("candidate_decision") or "").strip().lower()
        if decision in allowed:
            selected.append(row)
    return selected


def build_matrix(records: dict[str, dict[str, Any]], screening_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    matrix = []
    for screen in screening_rows:
        key = screen.get("dedupe_key") or screen.get("source_record_id") or screen.get("doi")
        record = records.get(key, {})
        row: dict[str, Any] = {
            "dedupe_key": key,
            "source": record.get("source", ""),
            "sources": "; ".join(record.get("sources", [])) if isinstance(record.get("sources"), list) else record.get("sources", ""),
            "source_record_id": record.get("source_record_id", ""),
            "doi": record.get("doi", ""),
            "title": record.get("title") or screen.get("title", ""),
            "authors": "; ".join(record.get("authors", [])) if isinstance(record.get("authors"), list) else record.get("authors", ""),
            "publication_year": record.get("publication_year") or screen.get("publication_year", ""),
            "venue": record.get("venue") or screen.get("venue", ""),
            "url": record.get("url", ""),
            "screening_decision": screen.get("reviewer_decision") or screen.get("candidate_decision", ""),
            "screening_reason": screen.get("reviewer_reason") or screen.get("candidate_reason", ""),
        }
        for field in EXTRACTION_FIELDS:
            row[field] = ""
        matrix.append(row)
    return matrix


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    base_fields = [
        "dedupe_key",
        "source",
        "sources",
        "source_record_id",
        "doi",
        "title",
        "authors",
        "publication_year",
        "venue",
        "url",
        "screening_decision",
        "screening_reason",
    ]
    fields = base_fields + EXTRACTION_FIELDS
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", default="data/processed/literature_records.jsonl")
    parser.add_argument("--screening", default="data/processed/screening_decisions.csv")
    parser.add_argument("--output", default="data/extraction_tables/evidence_matrix.csv")
    parser.add_argument("--include-maybe", action="store_true")
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

    records = read_jsonl(records_path)
    screening = selected_rows(read_screening(screening_path), args.include_maybe)
    matrix = build_matrix(records, screening)
    write_csv(Path(args.output), matrix)
    print(f"Wrote {len(matrix)} evidence matrix rows to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
