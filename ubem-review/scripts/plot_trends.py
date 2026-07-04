"""Create publication trend summaries and optional plots.

Counts are generated only from processed records or the evidence matrix.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_records(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".jsonl":
        return read_jsonl(path)
    return read_csv(path)


def year_counts(records: list[dict[str, Any]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for record in records:
        year = str(record.get("publication_year") or "").strip()
        if year.isdigit():
            counts[year] += 1
    return counts


def source_counts(records: list[dict[str, Any]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for record in records:
        source = str(record.get("source") or "unknown").strip() or "unknown"
        counts[source] += 1
    return counts


def write_counts(path: Path, counts: Counter[str], key_name: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow([key_name, "count"])
        for key in sorted(counts):
            writer.writerow([key, counts[key]])


def maybe_plot_years(path: Path, counts: Counter[str]) -> bool:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return False

    years = sorted(counts)
    values = [counts[year] for year in years]
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(8, 4.5))
    plt.bar(years, values, color="#3B6EA8")
    plt.xlabel("Publication year")
    plt.ylabel("Records")
    plt.title("UBEM literature records by year")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close()
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/processed/literature_records.jsonl")
    parser.add_argument("--year-csv", default="data/processed/trends_by_year.csv")
    parser.add_argument("--source-csv", default="data/processed/trends_by_source.csv")
    parser.add_argument("--figure", default="manuscript/figures/trends_by_year.png")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1

    records = read_records(input_path)
    years = year_counts(records)
    sources = source_counts(records)
    write_counts(Path(args.year_csv), years, "publication_year")
    write_counts(Path(args.source_csv), sources, "source")
    plotted = maybe_plot_years(Path(args.figure), years)
    print(f"Wrote trend CSV files for {len(records)} records")
    if plotted:
        print(f"Wrote figure to {args.figure}")
    else:
        print("matplotlib not installed; skipped PNG figure")
    return 0


if __name__ == "__main__":
    sys.exit(main())
