"""Deduplicate normalized review records and assign stable local paper IDs.

Deduplication is performed by normalized DOI first, then by normalized title
similarity. The script does not infer missing metadata.
"""

from __future__ import annotations

import argparse
from difflib import SequenceMatcher
import hashlib
import sys
from pathlib import Path

from review_schema import (
    DEDUPLICATED_COLUMNS,
    clean_space,
    ensure_identity,
    ensure_unique_citation_keys,
    normalize_doi,
    normalize_title,
    read_csv,
    write_csv,
)


def base_dedupe_key(row: dict[str, str]) -> str:
    doi = normalize_doi(row.get("DOI", ""))
    if doi:
        return f"doi:{doi}"
    title = normalize_title(row.get("title", ""))
    if title:
        return f"title:{title}"
    fallback = "|".join([row.get("source", ""), row.get("source_record_id", "")])
    return "source:" + hashlib.sha1(fallback.encode("utf-8")).hexdigest()[:16]


def title_similarity(left: str, right: str) -> float:
    left_norm = normalize_title(left)
    right_norm = normalize_title(right)
    if not left_norm or not right_norm:
        return 0.0
    return SequenceMatcher(None, left_norm, right_norm).ratio()


def merge(existing: dict[str, str], incoming: dict[str, str], method: str, score: float) -> dict[str, str]:
    merged = dict(existing)
    for key, value in incoming.items():
        if value and not merged.get(key):
            merged[key] = value
    sources = set(part for part in merged.get("sources", "").split("; ") if part)
    if incoming.get("source"):
        sources.add(incoming["source"])
    merged["sources"] = "; ".join(sorted(sources))
    merged["duplicate_count"] = str(int(merged.get("duplicate_count", "1")) + 1)

    existing_methods = set(part for part in merged.get("dedupe_method", "").split("; ") if part and part != "unique")
    existing_methods.add(method)
    merged["dedupe_method"] = "; ".join(sorted(existing_methods))
    previous_score = float(merged.get("dedupe_match_score") or "0")
    merged["dedupe_match_score"] = f"{max(previous_score, score):.3f}"
    return merged


def candidate_row(row: dict[str, str]) -> dict[str, str]:
    row = ensure_identity(row)
    return {
        "paper_id": "",
        "title": row.get("title", ""),
        "year": row.get("year", ""),
        "source": row.get("source", ""),
        "DOI": row.get("DOI", ""),
        "citation_key": row.get("citation_key", ""),
        "dedupe_key": base_dedupe_key(row),
        "dedupe_method": "unique",
        "dedupe_match_score": "1.000",
        "sources": row.get("source", ""),
        "source_record_id": row.get("source_record_id", ""),
        "publication_date": row.get("publication_date", ""),
        "authors": row.get("authors", ""),
        "venue": row.get("venue", ""),
        "publisher": row.get("publisher", ""),
        "url": row.get("url", ""),
        "abstract": row.get("abstract", ""),
        "keywords": row.get("keywords", ""),
        "duplicate_count": "1",
    }


def find_title_match(
    candidate: dict[str, str],
    retained: list[dict[str, str]],
    threshold: float,
) -> tuple[int | None, float]:
    best_index: int | None = None
    best_score = 0.0
    for index, existing in enumerate(retained):
        score = title_similarity(candidate.get("title", ""), existing.get("title", ""))
        if score > best_score:
            best_index = index
            best_score = score
    if best_index is not None and best_score >= threshold:
        return best_index, best_score
    return None, best_score


def assign_ids(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    for index, row in enumerate(rows, start=1):
        row["paper_id"] = f"P{index:05d}"
    return ensure_unique_citation_keys(rows)


def deduplicate(rows: list[dict[str, str]], title_threshold: float) -> list[dict[str, str]]:
    retained: list[dict[str, str]] = []
    doi_index: dict[str, int] = {}

    for row in rows:
        if not clean_space(row.get("title", "")):
            continue
        candidate = candidate_row(row)
        doi = normalize_doi(candidate.get("DOI", ""))
        if doi and doi in doi_index:
            existing_index = doi_index[doi]
            retained[existing_index] = merge(retained[existing_index], candidate, "doi", 1.0)
            continue

        title_index, score = find_title_match(candidate, retained, title_threshold)
        if title_index is not None:
            retained[title_index] = merge(retained[title_index], candidate, "title_similarity", score)
            if doi:
                doi_index[doi] = title_index
            continue

        if doi:
            doi_index[doi] = len(retained)
        retained.append(candidate)

    sorted_rows = sorted(retained, key=lambda item: (item.get("year", ""), item.get("title", "")))
    return assign_ids(sorted_rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/processed/all_records.csv")
    parser.add_argument("--output", default="data/processed/deduplicated_records.csv")
    parser.add_argument("--title-threshold", type=float, default=0.92)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1

    rows = deduplicate(read_csv(input_path), args.title_threshold)
    write_csv(Path(args.output), rows, DEDUPLICATED_COLUMNS)
    print(f"Wrote {len(rows)} deduplicated records")
    return 0


if __name__ == "__main__":
    sys.exit(main())
