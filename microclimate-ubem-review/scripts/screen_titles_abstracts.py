"""Apply inclusion/exclusion criteria to deduplicated title/abstract records.

The script performs a conservative first pass. It does not exclude records only
because an abstract is missing, and it keeps uncertain records for manual
review.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from review_schema import SCREENING_COLUMNS, clean_space, read_csv, write_csv


UBEM_TERMS = [
    "urban building energy modeling",
    "urban building energy modelling",
    "ubem",
    "district-scale building energy",
    "district scale building energy",
    "city-scale building energy",
    "city scale building energy",
    "building stock energy",
    "urban-scale building energy",
    "urban scale building energy",
]

MICROCLIMATE_TERMS = [
    "urban microclimate",
    "microclimate",
    "urban climate",
    "local weather",
    "local climate",
    "urban heat island",
    "uhi",
    "urban canopy",
    "urban canopy model",
    "ucm",
    "cfd",
    "envi-met",
    "envi met",
    "wrf",
    "uwg",
    "urban weather generator",
    "sensor-based weather",
    "sensor based weather",
    "weather correction",
]

ENERGY_OUTCOME_TERMS = [
    "energy demand",
    "energy consumption",
    "building energy",
    "heating",
    "cooling",
    "peak load",
    "thermal comfort",
    "overheating",
    "retrofit",
    "carbon",
    "emissions",
    "policy scenario",
    "policy",
]

SCALE_TERMS = [
    "neighborhood",
    "neighbourhood",
    "campus",
    "district",
    "city",
    "urban",
    "building stock",
    "stock",
]

REVIEW_TERMS = ["review", "survey", "state of the art", "state-of-the-art"]

OUT_OF_SCOPE_TERMS = [
    "single building",
    "single-building",
    "hvac control",
    "remote sensing",
    "land surface temperature",
]


def contains_any(text: str, terms: list[str]) -> list[str]:
    lower = text.lower()
    return [term for term in terms if term in lower]


def metadata_text(row: dict[str, str]) -> str:
    return " ".join(
        clean_space(row.get(field, ""))
        for field in ("title", "abstract", "keywords", "venue", "publisher")
    )


def abstract_available(row: dict[str, str]) -> str:
    return "yes" if clean_space(row.get("abstract", "")) else "no"


def confidence_for(decision: str, matched_groups: int, abstract_is_available: bool) -> str:
    if decision == "include" and matched_groups >= 3 and abstract_is_available:
        return "high"
    if decision == "exclude" and matched_groups == 0 and abstract_is_available:
        return "high"
    if decision == "uncertain" and not abstract_is_available:
        return "low"
    return "medium"


def screen_record(row: dict[str, str]) -> dict[str, str]:
    text = metadata_text(row)
    title = clean_space(row.get("title", ""))
    has_abstract = abstract_available(row) == "yes"

    ubem_matches = contains_any(text, UBEM_TERMS)
    micro_matches = contains_any(text, MICROCLIMATE_TERMS)
    outcome_matches = contains_any(text, ENERGY_OUTCOME_TERMS)
    scale_matches = contains_any(text, SCALE_TERMS)
    review_matches = contains_any(text, REVIEW_TERMS)
    out_matches = contains_any(text, OUT_OF_SCOPE_TERMS)

    matched_terms = sorted(set(ubem_matches + micro_matches + outcome_matches + scale_matches + review_matches + out_matches))
    matched_groups = sum(bool(matches) for matches in (ubem_matches, micro_matches, outcome_matches, scale_matches))

    if not title:
        decision = "uncertain"
        reason = "Insufficient title metadata; keep for manual review."
    elif ubem_matches and micro_matches and outcome_matches and scale_matches:
        decision = "include"
        reason = "Matches UBEM, microclimate, energy/performance outcome, and urban-scale criteria."
    elif review_matches and ubem_matches and micro_matches:
        decision = "include"
        reason = "Review article appears to address UBEM-microclimate coupling or urban weather transformation."
    elif ubem_matches and micro_matches and not outcome_matches:
        decision = "uncertain"
        reason = "Mentions UBEM and microclimate, but energy/performance outcome is unclear."
    elif not has_abstract and (ubem_matches or micro_matches or outcome_matches or scale_matches):
        decision = "uncertain"
        reason = "Abstract missing; metadata has partial scope signals, so record is retained for manual review."
    elif ubem_matches and not micro_matches:
        decision = "exclude"
        reason = "UBEM/building-energy signal is visible, but no microclimate relevance is visible in metadata."
    elif micro_matches and not (ubem_matches or outcome_matches):
        decision = "exclude"
        reason = "Microclimate or urban-climate signal is visible, but no building-energy outcome is visible."
    elif re.search(r"\b(remote sensing|hvac control|single[- ]building)\b", text, re.I) and not (ubem_matches and micro_matches):
        decision = "exclude"
        reason = "Metadata suggests an excluded topic without visible microclimate-aware UBEM link."
    elif not has_abstract:
        decision = "uncertain"
        reason = "Abstract missing and metadata is insufficient for reliable screening."
    else:
        decision = "exclude"
        reason = "No visible combination of UBEM, microclimate, urban scale, and energy/performance outcome."

    confidence = confidence_for(decision, matched_groups, has_abstract)
    return {
        "paper_id": row.get("paper_id", ""),
        "title": row.get("title", ""),
        "year": row.get("year", ""),
        "source": row.get("source", ""),
        "DOI": row.get("DOI", ""),
        "citation_key": row.get("citation_key", ""),
        "abstract_available": abstract_available(row),
        "screening_decision": decision,
        "reason": reason,
        "confidence": confidence,
        "matched_terms": "; ".join(matched_terms),
    }


def screen(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [screen_record(row) for row in rows]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/processed/deduplicated_records.csv")
    parser.add_argument("--output", default="data/processed/screening_results.csv")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1

    rows = screen(read_csv(input_path))
    write_csv(Path(args.output), rows, SCREENING_COLUMNS)
    print(f"Wrote screening decisions for {len(rows)} records")
    return 0


if __name__ == "__main__":
    sys.exit(main())
