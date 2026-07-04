"""Create a paper-level keyword term table for review scoping.

Each output row preserves paper identity columns, even though the row is a term
count, so downstream analysis can always be traced back to a paper.
"""

from __future__ import annotations

import argparse
import collections
import re
import sys
from pathlib import Path

from review_schema import IDENTITY_COLUMNS, read_csv, write_csv


STOPWORDS = {
    "and",
    "the",
    "for",
    "with",
    "from",
    "that",
    "this",
    "using",
    "energy",
    "building",
    "buildings",
    "urban",
}

OUTPUT_COLUMNS = IDENTITY_COLUMNS + ["term", "count"]


def tokenize(text: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-z][a-z0-9-]{2,}", text.lower())
        if token not in STOPWORDS
    ]


def analyze(rows: list[dict[str, str]], top_n_per_paper: int) -> list[dict[str, str]]:
    output = []
    for row in rows:
        text = " ".join(row.get(field, "") for field in ("title", "abstract", "keywords"))
        counts = collections.Counter(tokenize(text))
        for term, count in counts.most_common(top_n_per_paper):
            output.append(
                {
                    "paper_id": row.get("paper_id", ""),
                    "title": row.get("title", ""),
                    "year": row.get("year", ""),
                    "source": row.get("source", ""),
                    "DOI": row.get("DOI", ""),
                    "citation_key": row.get("citation_key", ""),
                    "term": term,
                    "count": str(count),
                }
            )
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/processed/deduplicated_records.csv")
    parser.add_argument("--output", default="data/processed/keyword_counts.csv")
    parser.add_argument("--top-n-per-paper", type=int, default=20)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1

    rows = analyze(read_csv(input_path), args.top_n_per_paper)
    write_csv(Path(args.output), rows, OUTPUT_COLUMNS)
    print(f"Wrote {len(rows)} paper-level keyword rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
