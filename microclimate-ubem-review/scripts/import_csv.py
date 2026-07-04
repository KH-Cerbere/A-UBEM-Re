"""Import local database CSV exports into normalized review records.

Place raw database exports under `data/raw/csv/`. The script maps common field
names from Scopus, Web of Science, Dimensions, or manually curated CSV files and
leaves missing metadata blank.
"""

from __future__ import annotations

import argparse
import csv
import glob
import sys
from datetime import datetime, timezone
from pathlib import Path

from review_schema import ALL_RECORDS_COLUMNS, append_csv, clean_space, ensure_identity, log_search


FIELD_ALIASES = {
    "title": ["title", "Title", "Article Title", "Document Title", "TI"],
    "year": ["year", "Year", "Publication Year", "PY"],
    "DOI": ["DOI", "doi", "DOI Link"],
    "citation_key": ["citation_key", "Citation Key", "BibTeX Key"],
    "source_record_id": ["source_record_id", "EID", "UT", "Accession Number", "Record ID"],
    "publication_date": ["publication_date", "Publication Date", "Date", "Published"],
    "authors": ["authors", "Authors", "Author", "AU"],
    "venue": ["venue", "Source title", "Source Title", "Journal", "Publication Name", "SO"],
    "publisher": ["publisher", "Publisher"],
    "url": ["url", "URL", "Link", "Document URL"],
    "abstract": ["abstract", "Abstract", "AB"],
    "keywords": ["keywords", "Author Keywords", "Index Keywords", "Keywords", "DE"],
}


def first_present(row: dict[str, str], names: list[str]) -> str:
    for name in names:
        if name in row and clean_space(row[name]):
            return clean_space(row[name])
    return ""


def normalize_row(row: dict[str, str], path: Path, fetched_at: str) -> dict[str, str]:
    normalized = {
        "paper_id": "",
        "title": first_present(row, FIELD_ALIASES["title"]),
        "year": first_present(row, FIELD_ALIASES["year"]),
        "source": "local_csv",
        "DOI": first_present(row, FIELD_ALIASES["DOI"]),
        "citation_key": first_present(row, FIELD_ALIASES["citation_key"]),
        "source_record_id": first_present(row, FIELD_ALIASES["source_record_id"]),
        "query": str(path),
        "fetched_at": fetched_at,
        "publication_date": first_present(row, FIELD_ALIASES["publication_date"]),
        "authors": first_present(row, FIELD_ALIASES["authors"]),
        "venue": first_present(row, FIELD_ALIASES["venue"]),
        "publisher": first_present(row, FIELD_ALIASES["publisher"]),
        "url": first_present(row, FIELD_ALIASES["url"]),
        "abstract": first_present(row, FIELD_ALIASES["abstract"]),
        "keywords": first_present(row, FIELD_ALIASES["keywords"]),
        "raw_file": str(path),
    }
    return ensure_identity(normalized)


def read_csv_export(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def expand_inputs(patterns: list[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        matches = [Path(match) for match in glob.glob(pattern)]
        paths.extend(matches if matches else [Path(pattern)])
    return [path for path in paths if path.exists()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", action="append", default=["data/raw/csv/*.csv"])
    parser.add_argument("--output", default="data/processed/all_records.csv")
    parser.add_argument("--search-log", default="logs/search_log.csv")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = expand_inputs(args.input)
    if not paths:
        print("No CSV files found.", file=sys.stderr)
        return 1

    fetched_at = datetime.now(timezone.utc).isoformat()
    normalized_rows: list[dict[str, str]] = []
    for path in paths:
        rows = read_csv_export(path)
        normalized_rows.extend(normalize_row(row, path, fetched_at) for row in rows)
        log_search(
            Path(args.search_log),
            source="local_csv",
            query=str(path),
            raw_output=str(path),
            normalized_output=args.output,
            records_returned=len(rows),
            notes="Local CSV import",
        )

    append_csv(Path(args.output), normalized_rows, ALL_RECORDS_COLUMNS)
    print(f"Wrote {len(normalized_rows)} CSV-derived records")
    return 0


if __name__ == "__main__":
    sys.exit(main())
