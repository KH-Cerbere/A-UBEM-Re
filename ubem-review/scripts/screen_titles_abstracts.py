"""Create a title and abstract screening table.

The default rule labels records as include/maybe/exclude candidates using
keywords only. Final decisions should be reviewed by a human.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any


INCLUDE_TERMS = [
    "urban building energy",
    "ubem",
    "city-scale building energy",
    "city scale building energy",
    "district-scale building energy",
    "urban energy model",
    "building stock energy",
    "large-scale building energy",
]
EXCLUDE_TERMS = ["mdpi", "mpdi"]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def contains_any(text: str, terms: list[str]) -> bool:
    text = text.lower()
    return any(term in text for term in terms)


def candidate_decision(record: dict[str, Any]) -> tuple[str, str]:
    haystack = " ".join(
        str(record.get(key) or "")
        for key in ("title", "abstract", "venue", "publisher", "url", "doi")
    )
    if contains_any(haystack, EXCLUDE_TERMS):
        return "exclude", "Identified MDPI/MPDI source metadata."
    if contains_any(haystack, INCLUDE_TERMS):
        return "include", "Keyword match in title, abstract, or metadata."
    if re.search(r"\b(building|buildings|urban|city|district|stock|energy)\b", haystack, re.I):
        return "maybe", "Partial topic match; needs reviewer check."
    return "exclude", "No UBEM-related keyword evidence in metadata."


def write_screening(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "dedupe_key",
        "source_record_id",
        "doi",
        "title",
        "publication_year",
        "venue",
        "candidate_decision",
        "candidate_reason",
        "reviewer_decision",
        "reviewer_reason",
        "notes",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            decision, reason = candidate_decision(record)
            writer.writerow(
                {
                    "dedupe_key": record.get("dedupe_key", ""),
                    "source_record_id": record.get("source_record_id", ""),
                    "doi": record.get("doi", ""),
                    "title": record.get("title", ""),
                    "publication_year": record.get("publication_year", ""),
                    "venue": record.get("venue", ""),
                    "candidate_decision": decision,
                    "candidate_reason": reason,
                    "reviewer_decision": "",
                    "reviewer_reason": "",
                    "notes": "",
                }
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/processed/literature_records.jsonl")
    parser.add_argument("--output", default="data/processed/screening_decisions.csv")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1

    records = read_jsonl(input_path)
    write_screening(Path(args.output), records)
    print(f"Wrote screening table for {len(records)} records to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
