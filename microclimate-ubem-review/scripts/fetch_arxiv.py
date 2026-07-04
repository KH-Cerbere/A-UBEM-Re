"""Fetch microclimate-UBEM candidate records from the arXiv API."""

from __future__ import annotations

import argparse
import json
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from review_schema import ALL_RECORDS_COLUMNS, append_csv, ensure_identity, log_search
from search_terms import default_queries


API_URL = "https://export.arxiv.org/api/query"
ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV = "{http://arxiv.org/schemas/atom}"
def text_of(parent: ET.Element, tag: str) -> str:
    child = parent.find(tag)
    return " ".join((child.text or "").split()) if child is not None else ""


def fetch_page(query: str, start: int, max_results: int) -> ET.Element:
    params = {
        "search_query": f'all:"{query}"',
        "start": start,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }
    request = Request(
        f"{API_URL}?{urlencode(params)}",
        headers={"User-Agent": "microclimate-ubem-review/0.1"},
    )
    with urlopen(request, timeout=60) as response:
        return ET.fromstring(response.read())


def iter_entries(query: str, max_results: int, batch_size: int, pause: float) -> list[ET.Element]:
    start = 0
    entries: list[ET.Element] = []
    while len(entries) < max_results:
        limit = min(batch_size, max_results - len(entries))
        feed = fetch_page(query, start, limit)
        page_entries = feed.findall(f"{ATOM}entry")
        if not page_entries:
            break
        entries.extend(page_entries)
        start += len(page_entries)
        time.sleep(pause)
    return entries


def normalize_entry(entry: ET.Element, query: str, fetched_at: str, raw_file: str) -> dict[str, str]:
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
    row = {
        "paper_id": "",
        "title": text_of(entry, f"{ATOM}title"),
        "year": published[:4] if len(published) >= 4 else "",
        "source": "arxiv",
        "DOI": text_of(entry, f"{ARXIV}doi"),
        "citation_key": "",
        "source_record_id": text_of(entry, f"{ATOM}id"),
        "query": query,
        "fetched_at": fetched_at,
        "publication_date": published,
        "authors": "; ".join(name for name in authors if name),
        "venue": "arXiv",
        "publisher": "arXiv",
        "url": links[0] if links else text_of(entry, f"{ATOM}id"),
        "abstract": text_of(entry, f"{ATOM}summary"),
        "keywords": "; ".join(categories),
        "raw_file": raw_file,
    }
    return ensure_identity(row)


def write_jsonl(path: Path, raw_entries: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for entry in raw_entries:
            handle.write(json.dumps({"raw_atom_entry": entry}, ensure_ascii=False) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", action="append", help="Search query. Can be repeated.")
    parser.add_argument("--max-results", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=25)
    parser.add_argument("--pause", type=float, default=3.0)
    parser.add_argument("--query-limit", type=int, default=30)
    parser.add_argument("--raw-output", default="data/raw/api/arxiv_works.jsonl")
    parser.add_argument("--csv-output", default="data/processed/all_records.csv")
    parser.add_argument("--search-log", default="logs/search_log.csv")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    fetched_at = datetime.now(timezone.utc).isoformat()
    raw_entries: list[str] = []
    normalized: list[dict[str, str]] = []

    for query in args.query or default_queries(args.query_limit):
        entries = iter_entries(query, args.max_results, args.batch_size, args.pause)
        raw_entries.extend(ET.tostring(entry, encoding="unicode") for entry in entries)
        normalized.extend(
            normalize_entry(entry, query, fetched_at, args.raw_output)
            for entry in entries
        )
        log_search(
            Path(args.search_log),
            source="arxiv",
            query=query,
            raw_output=args.raw_output,
            normalized_output=args.csv_output,
            records_returned=len(entries),
        )

    write_jsonl(Path(args.raw_output), raw_entries)
    append_csv(Path(args.csv_output), normalized, ALL_RECORDS_COLUMNS)
    print(f"Wrote {len(raw_entries)} arXiv records")
    return 0


if __name__ == "__main__":
    sys.exit(main())
