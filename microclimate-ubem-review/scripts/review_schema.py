"""Shared schema helpers for the microclimate-UBEM review repository."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import re
from pathlib import Path


IDENTITY_COLUMNS = ["paper_id", "title", "year", "source", "DOI", "citation_key"]

ALL_RECORDS_COLUMNS = IDENTITY_COLUMNS + [
    "source_record_id",
    "query",
    "fetched_at",
    "publication_date",
    "authors",
    "venue",
    "publisher",
    "url",
    "abstract",
    "keywords",
    "raw_file",
]

DEDUPLICATED_COLUMNS = IDENTITY_COLUMNS + [
    "dedupe_key",
    "dedupe_method",
    "dedupe_match_score",
    "sources",
    "source_record_id",
    "publication_date",
    "authors",
    "venue",
    "publisher",
    "url",
    "abstract",
    "keywords",
    "duplicate_count",
]

SEARCH_LOG_COLUMNS = [
    "searched_at",
    "source",
    "query",
    "raw_output",
    "normalized_output",
    "records_returned",
    "notes",
]

PRISMA_COLUMNS = ["stage", "count", "source_file", "notes"]

SCREENING_COLUMNS = IDENTITY_COLUMNS + [
    "abstract_available",
    "screening_decision",
    "reason",
    "confidence",
    "matched_terms",
]

EVIDENCE_COLUMNS = [
    "paper_id",
    "citation_key",
    "title",
    "year",
    "source",
    "DOI",
    "journal",
    "doi",
    "study_type",
    "review_or_original",
    "city",
    "country",
    "climate_zone",
    "spatial_scale",
    "building_type",
    "urban_form_variables",
    "microclimate_variable",
    "microclimate_data_source",
    "weather_file_type",
    "microclimate_model",
    "ubem_tool",
    "bem_engine",
    "coupling_strategy",
    "coupling_direction",
    "temporal_resolution",
    "spatial_resolution",
    "validation_data",
    "calibration_method",
    "uncertainty_method",
    "sensitivity_method",
    "energy_output",
    "comfort_output",
    "carbon_output",
    "policy_application",
    "key_finding",
    "reported_energy_impact",
    "reported_temperature_impact",
    "limitations",
    "reproducibility",
    "relevance_to_review",
]

MISSINGNESS_COLUMNS = ["field", "missing_count", "total_count", "missing_percent"]
VALIDATION_REPORT_COLUMNS = ["paper_id", "field", "value", "issue"]


STOPWORDS = {
    "a",
    "an",
    "and",
    "for",
    "in",
    "of",
    "on",
    "the",
    "to",
    "with",
    "using",
}


def clean_space(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_doi(value: object) -> str:
    text = clean_space(value).lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        text = text.removeprefix(prefix)
    return text


def normalize_title(value: object) -> str:
    text = re.sub(r"[^a-z0-9]+", " ", clean_space(value).lower())
    return clean_space(text)


def slug_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def first_author_token(authors: str) -> str:
    first = clean_space(authors).split(";")[0].strip()
    if not first:
        return ""
    if "," in first:
        first = first.split(",", 1)[0]
    parts = [part for part in re.split(r"\s+", first) if part]
    return slug_token(parts[-1]) if parts else ""


def first_title_token(title: str) -> str:
    for token in re.findall(r"[A-Za-z][A-Za-z0-9-]+", title):
        lower = token.lower()
        if lower not in STOPWORDS:
            return slug_token(lower)
    return "untitled"


def make_citation_key(row: dict[str, str]) -> str:
    existing = clean_space(row.get("citation_key", ""))
    if existing:
        return existing
    author = first_author_token(row.get("authors", "")) or "unknown"
    year = clean_space(row.get("year", "")) or "nd"
    title = first_title_token(row.get("title", ""))
    return f"{author}{year}{title}"


def ensure_identity(row: dict[str, str]) -> dict[str, str]:
    out = dict(row)
    out["paper_id"] = clean_space(out.get("paper_id", ""))
    out["title"] = clean_space(out.get("title", ""))
    out["year"] = clean_space(out.get("year", ""))
    out["source"] = clean_space(out.get("source", ""))
    out["DOI"] = normalize_doi(out.get("DOI") or out.get("doi", ""))
    out["citation_key"] = make_citation_key(out)
    return out


def ensure_unique_citation_keys(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: dict[str, int] = {}
    for row in rows:
        key = row.get("citation_key", "") or make_citation_key(row)
        seen[key] = seen.get(key, 0) + 1
        if seen[key] > 1:
            row["citation_key"] = f"{key}{seen[key]}"
        else:
            row["citation_key"] = key
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def append_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists() or path.stat().st_size == 0
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_search(
    log_path: Path,
    source: str,
    query: str,
    raw_output: str,
    normalized_output: str,
    records_returned: int,
    notes: str = "",
) -> None:
    append_csv(
        log_path,
        [
            {
                "searched_at": utc_now(),
                "source": source,
                "query": query,
                "raw_output": raw_output,
                "normalized_output": normalized_output,
                "records_returned": str(records_returned),
                "notes": notes,
            }
        ],
        SEARCH_LOG_COLUMNS,
    )
