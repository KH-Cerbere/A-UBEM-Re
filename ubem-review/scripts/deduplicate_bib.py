"""Deduplicate API JSONL records and local BibTeX exports.

Inputs are limited to files already present in data/raw_bib or explicitly
passed on the command line. Missing bibliographic fields are left blank.
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import re
import sys
from pathlib import Path
from typing import Any


DEFAULT_PATTERNS = ["data/raw_bib/*.jsonl", "data/raw_bib/*.bib"]


def clean_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def normalize_title(value: str) -> str:
    text = value.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return clean_space(text)


def normalize_doi(value: str) -> str:
    text = value.strip().lower()
    text = text.removeprefix("https://doi.org/")
    text = text.removeprefix("http://doi.org/")
    text = text.removeprefix("doi:")
    return text


def is_mdpi_text(*values: Any) -> bool:
    text = " ".join(str(value) for value in values if value).lower()
    return "mdpi" in text or "mpdi" in text


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSONL") from exc
    return rows


def split_bib_entries(text: str) -> list[str]:
    entries: list[str] = []
    start = None
    depth = 0
    for index, char in enumerate(text):
        if char == "@" and depth == 0:
            start = index
        if start is not None:
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    entries.append(text[start : index + 1])
                    start = None
    return entries


def parse_bib_fields(entry: str) -> dict[str, str]:
    header = re.match(r"@\w+\s*\{\s*([^,]+),", entry, re.S)
    record_id = clean_space(header.group(1)) if header else ""
    body = entry[header.end() :] if header else entry
    fields: dict[str, str] = {}

    for match in re.finditer(r"(\w+)\s*=\s*(\{(?:[^{}]|\{[^{}]*\})*\}|\"[^\"]*\"|[^,\n]+)", body, re.S):
        key = match.group(1).lower()
        value = match.group(2).strip().strip(",")
        if value.startswith("{") and value.endswith("}"):
            value = value[1:-1]
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        fields[key] = clean_space(value)

    fields["source_record_id"] = record_id
    return fields


def read_bibtex(path: Path) -> list[dict[str, Any]]:
    rows = []
    text = path.read_text(encoding="utf-8")
    for fields in split_bib_entries(text):
        parsed = parse_bib_fields(fields)
        rows.append(
            {
                "source": "local_bibtex",
                "source_record_id": parsed.get("source_record_id", ""),
                "query": "",
                "fetched_at": "",
                "doi": parsed.get("doi", ""),
                "title": parsed.get("title", ""),
                "publication_year": parsed.get("year", ""),
                "publication_date": parsed.get("date", ""),
                "authors": [clean_space(part) for part in parsed.get("author", "").split(" and ") if part.strip()],
                "venue": parsed.get("journal") or parsed.get("booktitle") or parsed.get("publisher") or "",
                "publisher": parsed.get("publisher", ""),
                "url": parsed.get("url", ""),
                "abstract": parsed.get("abstract", ""),
                "raw": parsed,
            }
        )
    return rows


def read_records(paths: list[Path]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in paths:
        if path.suffix.lower() == ".jsonl":
            records.extend(read_jsonl(path))
        elif path.suffix.lower() == ".bib":
            records.extend(read_bibtex(path))
    return records


def dedupe_key(record: dict[str, Any]) -> str:
    doi = normalize_doi(str(record.get("doi") or ""))
    if doi:
        return f"doi:{doi}"
    title = normalize_title(str(record.get("title") or ""))
    if title:
        return f"title:{title}"
    source = record.get("source") or ""
    source_id = record.get("source_record_id") or ""
    return f"source:{source}:{source_id}"


def merge_records(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = dict(existing)
    for key, value in incoming.items():
        if key == "raw":
            continue
        if not merged.get(key) and value:
            merged[key] = value
    sources = set(merged.get("sources") or [merged.get("source", "")])
    if incoming.get("source"):
        sources.add(incoming["source"])
    merged["sources"] = sorted(source for source in sources if source)
    merged.setdefault("duplicates", [])
    merged["duplicates"].append(
        {
            "source": incoming.get("source", ""),
            "source_record_id": incoming.get("source_record_id", ""),
            "doi": incoming.get("doi", ""),
            "title": incoming.get("title", ""),
        }
    )
    return merged


def deduplicate(records: list[dict[str, Any]], exclude_mdpi: bool) -> list[dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    for record in records:
        if not record.get("title"):
            continue
        if exclude_mdpi and is_mdpi_text(
            record.get("venue"),
            record.get("publisher"),
            record.get("url"),
            record.get("doi"),
        ):
            continue
        key = dedupe_key(record)
        if key in by_key:
            by_key[key] = merge_records(by_key[key], record)
        else:
            row = dict(record)
            row["dedupe_key"] = key
            row["sources"] = [row.get("source", "")]
            row["duplicates"] = []
            row.pop("raw", None)
            by_key[key] = row
    return sorted(by_key.values(), key=lambda row: (str(row.get("publication_year", "")), str(row.get("title", ""))))


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "dedupe_key",
        "source",
        "sources",
        "source_record_id",
        "doi",
        "title",
        "publication_year",
        "venue",
        "publisher",
        "url",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: json.dumps(row.get(field), ensure_ascii=False) if isinstance(row.get(field), list) else row.get(field, "") for field in fields})


def expand_inputs(inputs: list[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in inputs:
        matches = [Path(match) for match in glob.glob(pattern)]
        paths.extend(matches if matches else [Path(pattern)])
    return [path for path in paths if path.exists()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", action="append", help="Input JSONL/BibTeX file or glob. Can be repeated.")
    parser.add_argument("--output-jsonl", default="data/processed/literature_records.jsonl")
    parser.add_argument("--output-csv", default="data/processed/literature_records.csv")
    parser.add_argument(
        "--include-mdpi",
        action="store_true",
        help="Keep MDPI/MPDI records instead of excluding identifiable records.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_patterns = args.input or DEFAULT_PATTERNS
    paths = expand_inputs(input_patterns)
    if not paths:
        print("No input files found. Add API JSONL or BibTeX files to data/raw_bib.", file=sys.stderr)
        return 1

    records = read_records(paths)
    deduped = deduplicate(records, exclude_mdpi=not args.include_mdpi)
    write_jsonl(Path(args.output_jsonl), deduped)
    write_csv(Path(args.output_csv), deduped)
    print(f"Read {len(records)} records from {len(paths)} files")
    print(f"Wrote {len(deduped)} deduplicated records")
    return 0


if __name__ == "__main__":
    sys.exit(main())
