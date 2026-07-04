"""Fetch microclimate-UBEM candidate records from the OpenAlex Works API.

This script reads only from a documented public API and writes raw API records
plus normalized local metadata. It does not infer missing paper content.
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

from review_schema import ALL_RECORDS_COLUMNS, append_csv, ensure_identity, log_search
from search_terms import default_queries


API_URL = "https://api.openalex.org/works"
def reconstruct_abstract(index: dict[str, list[int]] | None) -> str:
    if not index:
        return ""
    words: list[tuple[int, str]] = []
    for word, positions in index.items():
        for position in positions:
            words.append((position, word))
    return " ".join(word for _, word in sorted(words))


def author_names(work: dict[str, Any]) -> str:
    names = []
    for authorship in work.get("authorships") or []:
        author = authorship.get("author") or {}
        if author.get("display_name"):
            names.append(author["display_name"])
    return "; ".join(names)


def fetch_page(query: str, per_page: int, cursor: str) -> dict[str, Any]:
    params = {"search": query, "per-page": per_page, "cursor": cursor}
    request = Request(
        f"{API_URL}?{urlencode(params)}",
        headers={"User-Agent": "microclimate-ubem-review/0.1"},
    )
    with urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def iter_records(query: str, max_results: int, per_page: int, pause: float) -> list[dict[str, Any]]:
    cursor = "*"
    records: list[dict[str, Any]] = []
    while len(records) < max_results:
        page = fetch_page(query, per_page, cursor)
        results = page.get("results") or []
        if not results:
            break
        records.extend(results[: max_results - len(records)])
        next_cursor = (page.get("meta") or {}).get("next_cursor")
        if not next_cursor or next_cursor == cursor:
            break
        cursor = next_cursor
        time.sleep(pause)
    return records


def normalize_work(work: dict[str, Any], query: str, fetched_at: str, raw_file: str) -> dict[str, str]:
    primary_location = work.get("primary_location") or {}
    source = primary_location.get("source") or {}
    concepts = [
        concept.get("display_name", "")
        for concept in work.get("concepts") or []
        if concept.get("display_name")
    ]
    row = {
        "paper_id": "",
        "title": work.get("title") or "",
        "year": str(work.get("publication_year") or ""),
        "source": "openalex",
        "DOI": work.get("doi") or "",
        "citation_key": "",
        "source_record_id": work.get("id") or "",
        "query": query,
        "fetched_at": fetched_at,
        "publication_date": work.get("publication_date") or "",
        "authors": author_names(work),
        "venue": source.get("display_name") or "",
        "publisher": work.get("publisher") or source.get("host_organization_name") or "",
        "url": primary_location.get("landing_page_url") or work.get("id") or "",
        "abstract": reconstruct_abstract(work.get("abstract_inverted_index")),
        "keywords": "; ".join(concepts),
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
    parser.add_argument("--per-page", type=int, default=50)
    parser.add_argument("--pause", type=float, default=0.2)
    parser.add_argument("--query-limit", type=int, default=60)
    parser.add_argument("--raw-output", default="data/raw/api/openalex_works.jsonl")
    parser.add_argument("--csv-output", default="data/processed/all_records.csv")
    parser.add_argument("--search-log", default="logs/search_log.csv")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    fetched_at = datetime.now(timezone.utc).isoformat()
    raw_records: list[dict[str, Any]] = []
    normalized: list[dict[str, str]] = []

    for query in args.query or default_queries(args.query_limit):
        query_records = iter_records(query, args.max_results, args.per_page, args.pause)
        raw_records.extend(query_records)
        normalized.extend(
            normalize_work(record, query, fetched_at, args.raw_output)
            for record in query_records
        )
        log_search(
            Path(args.search_log),
            source="openalex",
            query=query,
            raw_output=args.raw_output,
            normalized_output=args.csv_output,
            records_returned=len(query_records),
        )

    write_jsonl(Path(args.raw_output), raw_records)
    append_csv(Path(args.csv_output), normalized, ALL_RECORDS_COLUMNS)
    print(f"Wrote {len(raw_records)} OpenAlex records")
    return 0


if __name__ == "__main__":
    sys.exit(main())
