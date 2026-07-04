"""Fetch Urban Building Energy Modeling records from arXiv.

This script writes only records returned by the arXiv API. It does not invent
missing metadata.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_URL = "https://export.arxiv.org/api/query"
ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV = "{http://arxiv.org/schemas/atom}"
DEFAULT_QUERIES = [
    "urban building energy modeling",
    "city-scale building energy simulation",
    "urban energy modeling buildings",
]


def text_of(parent: ET.Element, tag: str) -> str:
    child = parent.find(tag)
    return (child.text or "").strip() if child is not None else ""


def normalize_entry(entry: ET.Element, query: str, fetched_at: str) -> dict[str, Any]:
    authors = [text_of(author, f"{ATOM}name") for author in entry.findall(f"{ATOM}author")]
    links = [
        link.attrib.get("href", "")
        for link in entry.findall(f"{ATOM}link")
        if link.attrib.get("href")
    ]
    categories = [
        category.attrib.get("term", "")
        for category in entry.findall(f"{ATOM}category")
        if category.attrib.get("term")
    ]
    published = text_of(entry, f"{ATOM}published")
    year = published[:4] if len(published) >= 4 else ""

    return {
        "source": "arxiv",
        "source_record_id": text_of(entry, f"{ATOM}id"),
        "query": query,
        "fetched_at": fetched_at,
        "doi": text_of(entry, f"{ARXIV}doi"),
        "title": " ".join(text_of(entry, f"{ATOM}title").split()),
        "publication_year": year,
        "publication_date": published,
        "authors": [name for name in authors if name],
        "venue": "arXiv",
        "publisher": "arXiv",
        "url": links[0] if links else text_of(entry, f"{ATOM}id"),
        "abstract": " ".join(text_of(entry, f"{ATOM}summary").split()),
        "categories": categories,
        "raw": ET.tostring(entry, encoding="unicode"),
    }


def fetch_page(query: str, start: int, max_results: int) -> ET.Element:
    params = {
        "search_query": f'all:"{query}"',
        "start": start,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }
    url = f"{API_URL}?{urlencode(params)}"
    request = Request(url, headers={"User-Agent": "ubem-review/0.1"})
    with urlopen(request, timeout=60) as response:
        return ET.fromstring(response.read())


def iter_records(query: str, max_results: int, batch_size: int, pause: float) -> list[dict[str, Any]]:
    fetched_at = datetime.now(timezone.utc).isoformat()
    records: list[dict[str, Any]] = []
    start = 0

    while len(records) < max_results:
        limit = min(batch_size, max_results - len(records))
        feed = fetch_page(query, start, limit)
        entries = feed.findall(f"{ATOM}entry")
        if not entries:
            break
        for entry in entries:
            records.append(normalize_entry(entry, query, fetched_at))
        start += len(entries)
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
    parser.add_argument("--max-results", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=25)
    parser.add_argument("--pause", type=float, default=3.0)
    parser.add_argument(
        "--output",
        default="data/raw_bib/arxiv_works.jsonl",
        help="Output JSONL file.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    queries = args.query or DEFAULT_QUERIES
    all_rows: list[dict[str, Any]] = []

    for query in queries:
        all_rows.extend(iter_records(query, args.max_results, args.batch_size, args.pause))

    write_jsonl(Path(args.output), all_rows)
    print(f"Wrote {len(all_rows)} arXiv records to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
