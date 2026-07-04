"""Search term groups and query builders for the microclimate-aware UBEM review."""

from __future__ import annotations

import argparse
from itertools import product


TERM_GROUPS = {
    "A_UBEM_core": [
        "urban building energy modeling",
        "urban building energy modelling",
        "UBEM",
        "city-scale building energy simulation",
        "district-scale building energy modeling",
        "building stock energy modeling",
    ],
    "B_microclimate_core": [
        "urban microclimate",
        "urban heat island",
        "local climate",
        "urban climate",
        "urban canopy model",
        "microclimate data",
    ],
    "C_coupling": [
        "coupling",
        "co-simulation",
        "integrated model",
        "weather file transformation",
        "urban weather generator",
        "WRF",
        "ENVI-met",
        "CFD",
        "UCM",
    ],
    "D_evaluation": [
        "uncertainty",
        "validation",
        "calibration",
        "sensitivity analysis",
        "energy demand",
        "cooling demand",
        "heating demand",
        "overheating",
        "thermal comfort",
    ],
}


def quote(term: str) -> str:
    if " " in term or "-" in term:
        return f'"{term}"'
    return term


def compact_boolean_query() -> str:
    groups = []
    for terms in TERM_GROUPS.values():
        groups.append("(" + " OR ".join(quote(term) for term in terms) + ")")
    return " AND ".join(groups)


def simple_queries(include_coupling: bool = True, include_evaluation: bool = True) -> list[str]:
    """Build API-friendly queries from A+B+C and A+B+D combinations.

    Full A x B x C x D expansion is usually too large for public APIs, so the
    default search set combines every UBEM term with every microclimate term and
    one coupling or evaluation term at a time.
    """
    queries: list[str] = []
    a_terms = TERM_GROUPS["A_UBEM_core"]
    b_terms = TERM_GROUPS["B_microclimate_core"]
    if include_coupling:
        for a_term, b_term, c_term in product(a_terms, b_terms, TERM_GROUPS["C_coupling"]):
            queries.append(f"{a_term} {b_term} {c_term}")
    if include_evaluation:
        for a_term, b_term, d_term in product(a_terms, b_terms, TERM_GROUPS["D_evaluation"]):
            queries.append(f"{a_term} {b_term} {d_term}")
    return queries


def default_queries(limit: int | None = 60) -> list[str]:
    queries = simple_queries()
    return queries[:limit] if limit else queries


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=["simple", "boolean"], default="simple")
    parser.add_argument("--limit", type=int, default=60)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.format == "boolean":
        print(compact_boolean_query())
    else:
        for query in default_queries(args.limit):
            print(query)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
