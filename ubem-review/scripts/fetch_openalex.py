"""Fetch Urban Building Energy Modeling records from OpenAlex.

This script writes only records returned by the OpenAlex API. It does not
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


API_URL = "https://api.openalex.org/works"
DEFAULT_QUERIES = [
    "urban building energy modeling",
    "urban building energy modelling",
    "UBEM building energy",
    "city-scale building energy simulation",
    "urban energy modeling buildings",
    "building stock energy modeling urban",
]


def reconstruct_abstract(index: dict[str, list[int]] | None) -> str:
    if not index:
        return ""
    words: list[tuple[int, str]] = []
    for word, positions in index.items():
        for position in positions:
            words.append((position, word))
    return " ".join(word for _, word in sorted(words))


def is_mdpi_record(work: dict[str, Any]) -> bool:
    haystack: list[str] = []
    for key in ("publisher", "doi", "id"):
        value = work.get(key)
        if isinstance(value, str):
            haystack.append(value)

    primary_location = work.get("primary_location") or {}
    source = primary_location.get("source") or {}
    for key in ("display_name", "host_organization_name", "homepage_url"):
        value = source.get(key)
        if isinstance(value, str):
            haystack.append(value)

    for location in work.get("locations") or []:
        landing = location.get("landing_page_url")
        pdf = location.get("pdf_url")
        if isinstance(landing, str):
            haystack.append(landing)
        if isinstance(pdf, str):
            haystack.append(pdf)

    text = " ".join(haystack).lower()
    return "mdpi" in text or "mpdi" in text


def normalize_work(work: dict[str, Any], query: str, fetched_at: str) -> dict[str, Any]:
    authors = []
    for authorship in work.get("authorships") or []:
        author = authorship.get("author") or {}
        name = author.get("display_name")
        if name:
            authors.append(name)

    primary_location = work.get("primary_location") or {}
    source = primary_location.get("source") or {}

    return {
        "source": "openalex",
        "source_record_id": work.get("id") or "",
        "query": query,
        "fetched_at": fetched_at,
        "doi": work.get("doi") or "",
        "title": work.get("title") or "",
        "publication_year": work.get("publication_year") or "",
        "publication_date": work.get("publication_date") or "",
        "authors": authors,
        "venue": source.get("display_name") or "",
        "publisher": work.get("publisher") or source.get("host_organization_name") or "",
        "url": work.get("id") or primary_location.get("landing_page_url") or "",
        "abstract": reconstruct_abstract(work.get("abstract_inverted_index")),
        "raw": work,
    }


def fetch_page(query: str, per_page: int, cursor: str) -> dict[str, Any]:
    params = {
        "search": query,
        "per-page": per_page,
        "cursor": cursor,
    }
    url = f"{API_URL}?{urlencode(params)}"
    request = Request(url, headers={"User-Agent": "ubem-review/0.1"})
    with urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def iter_records(
    query: str,
    max_results: int,
    per_page: int,
    exclude_mdpi: bool,
    pause: float,
) -> list[dict[str, Any]]:
    fetched_at = datetime.now(timezone.utc).isoformat()
    cursor = "*"
    records: list[dict[str, Any]] = []

    while len(records) < max_results:
        page = fetch_page(query, per_page, cursor)
        results = page.get("results") or []
        if not results:
            break

        for work in results:
            if exclude_mdpi and is_mdpi_record(work):
                continue
            records.append(normalize_work(work, query, fetched_at))
            if len(records) >= max_results:
                break

        next_cursor = (page.get("meta") or {}).get("next_cursor")
        if not next_cursor or next_cursor == cursor:
            break
        cursor = next_cursor
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
    parser.add_argument("--per-page", type=int, default=50)
    parser.add_argument("--pause", type=float, default=0.2)
    parser.add_argument(
        "--output",
        default="data/raw_bib/openalex_works.jsonl",
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
            per_page=args.per_page,
            exclude_mdpi=not args.include_mdpi,
            pause=args.pause,
        )
        all_rows.extend(rows)

    write_jsonl(Path(args.output), all_rows)
    print(f"Wrote {len(all_rows)} OpenAlex records to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
