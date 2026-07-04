"""Fetch Urban Building Energy Modeling records from Crossref.

This script writes only records returned by the Crossref API. It does not
invent missing metadata and excludes MDPI/MPDI records when identifiable.
"""

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


API_URL = "https://api.crossref.org/works"
DEFAULT_QUERIES = [
    "urban building energy modeling",
    "city-scale building energy simulation",
    "urban energy modeling buildings",
    "building stock energy modeling urban",
]


def first(values: Any) -> str:
    if isinstance(values, list) and values:
        return str(values[0])
    if isinstance(values, str):
        return values
    return ""


def issued_year(item: dict[str, Any]) -> str:
    issued = item.get("issued") or item.get("published-print") or item.get("published-online") or {}
    date_parts = issued.get("date-parts") or []
    if date_parts and date_parts[0]:
        return str(date_parts[0][0])
    return ""


def author_names(item: dict[str, Any]) -> list[str]:
    names = []
    for author in item.get("author") or []:
        given = author.get("given") or ""
        family = author.get("family") or ""
        name = " ".join(part for part in (given, family) if part).strip()
        if name:
            names.append(name)
    return names


def is_mdpi_record(item: dict[str, Any]) -> bool:
    haystack: list[str] = []
    for key in ("publisher", "DOI", "URL", "ISSN"):
        value = item.get(key)
        if isinstance(value, str):
            haystack.append(value)
        elif isinstance(value, list):
            haystack.extend(str(part) for part in value)
    for key in ("container-title", "short-container-title"):
        value = item.get(key)
        if isinstance(value, list):
            haystack.extend(str(part) for part in value)
    text = " ".join(haystack).lower()
    return "mdpi" in text or "mpdi" in text


def normalize_item(item: dict[str, Any], query: str, fetched_at: str) -> dict[str, Any]:
    doi = item.get("DOI") or ""
    return {
        "source": "crossref",
        "source_record_id": doi,
        "query": query,
        "fetched_at": fetched_at,
        "doi": doi,
        "title": first(item.get("title")),
        "publication_year": issued_year(item),
        "publication_date": item.get("published-print") or item.get("published-online") or item.get("issued") or "",
        "authors": author_names(item),
        "venue": first(item.get("container-title")),
        "publisher": item.get("publisher") or "",
        "url": item.get("URL") or "",
        "abstract": item.get("abstract") or "",
        "raw": item,
    }


def fetch_page(query: str, rows: int, offset: int) -> dict[str, Any]:
    params = {
        "query": query,
        "rows": rows,
        "offset": offset,
    }
    url = f"{API_URL}?{urlencode(params)}"
    request = Request(url, headers={"User-Agent": "ubem-review/0.1 (mailto:example@example.com)"})
    with urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def iter_records(
    query: str,
    max_results: int,
    rows: int,
    exclude_mdpi: bool,
    pause: float,
) -> list[dict[str, Any]]:
    fetched_at = datetime.now(timezone.utc).isoformat()
    offset = 0
    records: list[dict[str, Any]] = []

    while len(records) < max_results:
        page = fetch_page(query, rows, offset)
        items = ((page.get("message") or {}).get("items")) or []
        if not items:
            break
        for item in items:
            if exclude_mdpi and is_mdpi_record(item):
                continue
            records.append(normalize_item(item, query, fetched_at))
            if len(records) >= max_results:
                break
        offset += rows
        time.sleep(pause)

    return records


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", action="append", help="Search query. Can be repeated.")
    parser.add_argument("--max-results", type=int, default=100)
    parser.add_argument("--rows", type=int, default=50)
    parser.add_argument("--pause", type=float, default=0.2)
    parser.add_argument(
        "--output",
        default="data/raw_bib/crossref_works.jsonl",
        help="Output JSONL file.",
    )
    parser.add_argument(
        "--include-mdpi",
        action="store_true",
        help="Keep MDPI/MPDI records instead of excluding identifiable records.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    queries = args.query or DEFAULT_QUERIES
    all_rows: list[dict[str, Any]] = []

    for query in queries:
        rows = iter_records(
            query=query,
            max_results=args.max_results,
            rows=args.rows,
            exclude_mdpi=not args.include_mdpi,
            pause=args.pause,
        )
        all_rows.extend(rows)

    write_jsonl(Path(args.output), all_rows)
    print(f"Wrote {len(all_rows)} Crossref records to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
