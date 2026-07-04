"""Convert local BibTeX exports into normalized review records.

The script reads local files only. It preserves missing fields as blanks and
does not invent metadata.
"""

from __future__ import annotations

import argparse
import glob
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from review_schema import ALL_RECORDS_COLUMNS, append_csv, clean_space, ensure_identity, log_search


def split_bib_entries(text: str) -> list[str]:
    entries: list[str] = []
    start = None
    depth = 0
    for index, char in enumerate(text):
        if char == "@" and depth == 0:
            start = index
        if start is not None:
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    entries.append(text[start : index + 1])
                    start = None
    return entries


def parse_bib_fields(entry: str) -> dict[str, str]:
    header = re.match(r"@\w+\s*\{\s*([^,]+),", entry, re.S)
    source_record_id = clean_space(header.group(1)) if header else ""
    body = entry[header.end() :] if header else entry
    fields: dict[str, str] = {"source_record_id": source_record_id}
    pattern = r"(\w+)\s*=\s*(\{(?:[^{}]|\{[^{}]*\})*\}|\"[^\"]*\"|[^,\n]+)"
    for match in re.finditer(pattern, body, re.S):
        key = match.group(1).lower()
        value = match.group(2).strip().strip(",")
        if value.startswith("{") and value.endswith("}"):
            value = value[1:-1]
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        fields[key] = clean_space(value)
    return fields


def row_from_bib(fields: dict[str, str], path: Path, fetched_at: str) -> dict[str, str]:
    row = {
        "paper_id": "",
        "title": fields.get("title", ""),
        "year": fields.get("year", ""),
        "source": "local_bibtex",
        "DOI": fields.get("doi", ""),
        "citation_key": fields.get("source_record_id", ""),
        "source_record_id": fields.get("source_record_id", ""),
        "query": "",
        "fetched_at": fetched_at,
        "publication_date": fields.get("date", ""),
        "authors": "; ".join(
            part.strip() for part in fields.get("author", "").split(" and ") if part.strip()
        ),
        "venue": fields.get("journal") or fields.get("booktitle") or fields.get("publisher") or "",
        "publisher": fields.get("publisher", ""),
        "url": fields.get("url", ""),
        "abstract": fields.get("abstract", ""),
        "keywords": fields.get("keywords", ""),
        "raw_file": str(path),
    }
    return ensure_identity(row)


def expand_inputs(patterns: list[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        matches = [Path(match) for match in glob.glob(pattern)]
        paths.extend(matches if matches else [Path(pattern)])
    return [path for path in paths if path.exists()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", action="append", default=["data/raw/bibtex/*.bib"])
    parser.add_argument("--output", default="data/processed/all_records.csv")
    parser.add_argument("--search-log", default="logs/search_log.csv")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = expand_inputs(args.input)
    if not paths:
        print("No BibTeX files found.", file=sys.stderr)
        return 1

    fetched_at = datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, str]] = []
    for path in paths:
        before = len(rows)
        for entry in split_bib_entries(path.read_text(encoding="utf-8")):
            rows.append(row_from_bib(parse_bib_fields(entry), path, fetched_at))
        log_search(
            Path(args.search_log),
            source="local_bibtex",
            query=str(path),
            raw_output=str(path),
            normalized_output=args.output,
            records_returned=len(rows) - before,
            notes="Local BibTeX import",
        )

    append_csv(Path(args.output), rows, ALL_RECORDS_COLUMNS)
    print(f"Wrote {len(rows)} BibTeX-derived records")
    return 0


if __name__ == "__main__":
    sys.exit(main())
