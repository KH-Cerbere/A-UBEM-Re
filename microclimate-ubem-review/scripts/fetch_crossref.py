"""Fetch microclimate-UBEM candidate records from the Crossref Works API."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from review_schema import ALL_RECORDS_COLUMNS, append_csv, ensure_identity, log_search
from search_terms import default_queries


API_URL = "https://api.crossref.org/works"
def first(value: Any) -> str:
    if isinstance(value, list) and value:
        return str(value[0])
    if isinstance(value, str):
        return value
    return ""


def issued_year(item: dict[str, Any]) -> str:
    issued = item.get("issued") or item.get("published-print") or item.get("published-online") or {}
    date_parts = issued.get("date-parts") or []
    if date_parts and date_parts[0]:
        return str(date_parts[0][0])
    return ""


def author_names(item: dict[str, Any]) -> str:
    names = []
    for author in item.get("author") or []:
        given = author.get("given") or ""
        family = author.get("family") or ""
        name = " ".join(part for part in (given, family) if part).strip()
        if name:
            names.append(name)
    return "; ".join(names)


def fetch_page(query: str, rows: int, offset: int) -> dict[str, Any]:
    params = {"query": query, "rows": rows, "offset": offset}
    request = Request(
        f"{API_URL}?{urlencode(params)}",
        headers={"User-Agent": "microclimate-ubem-review/0.1"},
    )
    with urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def iter_records(query: str, max_results: int, rows: int, pause: float) -> list[dict[str, Any]]:
    offset = 0
    records: list[dict[str, Any]] = []
    while len(records) < max_results:
        page = fetch_page(query, rows, offset)
        items = ((page.get("message") or {}).get("items")) or []
        if not items:
            break
        records.extend(items[: max_results - len(records)])
        offset += rows
        time.sleep(pause)
    return records


def normalize_item(item: dict[str, Any], query: str, fetched_at: str, raw_file: str) -> dict[str, str]:
    row = {
        "paper_id": "",
        "title": first(item.get("title")),
        "year": issued_year(item),
        "source": "crossref",
        "DOI": item.get("DOI") or "",
        "citation_key": "",
        "source_record_id": item.get("DOI") or item.get("URL") or "",
        "query": query,
        "fetched_at": fetched_at,
        "publication_date": json.dumps(item.get("issued") or "", ensure_ascii=False),
        "authors": author_names(item),
        "venue": first(item.get("container-title")),
        "publisher": item.get("publisher") or "",
        "url": item.get("URL") or "",
        "abstract": item.get("abstract") or "",
        "keywords": "; ".join(str(term) for term in item.get("subject") or []),
        "raw_file": raw_file,
    }
    return ensure_identity(row)


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", action="append", help="Search query. Can be repeated.")
    parser.add_argument("--max-results", type=int, default=100)
    parser.add_argument("--rows", type=int, default=50)
    parser.add_argument("--pause", type=float, default=0.2)
    parser.add_argument("--query-limit", type=int, default=60)
    parser.add_argument("--raw-output", default="data/raw/api/crossref_works.jsonl")
    parser.add_argument("--csv-output", default="data/processed/all_records.csv")
    parser.add_argument("--search-log", default="logs/search_log.csv")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    fetched_at = datetime.now(timezone.utc).isoformat()
    raw_records: list[dict[str, Any]] = []
    normalized: list[dict[str, str]] = []

    for query in args.query or default_queries(args.query_limit):
        query_records = iter_records(query, args.max_results, args.rows, args.pause)
        raw_records.extend(query_records)
        normalized.extend(
            normalize_item(record, query, fetched_at, args.raw_output)
            for record in query_records
        )
        log_search(
            Path(args.search_log),
            source="crossref",
            query=query,
            raw_output=args.raw_output,
            normalized_output=args.csv_output,
            records_returned=len(query_records),
        )

    write_jsonl(Path(args.raw_output), raw_records)
    append_csv(Path(args.csv_output), normalized, ALL_RECORDS_COLUMNS)
    print(f"Wrote {len(raw_records)} Crossref records")
    return 0


if __name__ == "__main__":
    sys.exit(main())
