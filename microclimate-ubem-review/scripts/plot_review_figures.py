"""Generate publication-oriented review figures from the evidence matrix.

The script does not fabricate values. Empty or missing evidence produces empty
figures, missingness warnings, and captions that avoid unsupported claims.
"""

from __future__ import annotations

import argparse
import collections
import csv
import math
from pathlib import Path
from typing import Iterable

from review_schema import read_csv


NOT_REPORTED = "not reported"

FIGURE_SPECS = {
    "figure_1_prisma_flow": {
        "title": "PRISMA flow diagram",
        "fields": [],
        "caption": "Figure 1. PRISMA flow diagram summarizing the number of records identified, deduplicated, screened, excluded, assessed for full text, and included. It supports the transparency claim for the review workflow, not a substantive finding about the literature.",
    },
    "figure_2_annual_publication_trend": {
        "title": "Annual publication trend",
        "fields": ["year"],
        "caption": "Figure 2. Annual publication trend of microclimate-aware UBEM studies in the extracted evidence matrix. It supports a descriptive claim about publication timing only when records are present.",
    },
    "figure_3_microclimate_variable_by_ubem_output_heatmap": {
        "title": "Microclimate variable x UBEM output",
        "fields": ["microclimate_variable", "energy_output", "comfort_output", "carbon_output"],
        "caption": "Figure 3. Heatmap linking reported microclimate variables with UBEM output categories. It supports evidence synthesis about which microclimate inputs are connected to which modeled outcomes.",
    },
    "figure_4_data_source_coupling_energy_output_sankey": {
        "title": "Data source -> coupling strategy -> energy output",
        "fields": ["microclimate_data_source", "coupling_strategy", "energy_output"],
        "caption": "Figure 4. Sankey-style flow from microclimate data source to coupling strategy and energy output. It supports synthesis of the methodological pathway from data to energy-performance evidence.",
    },
    "figure_5_tool_map": {
        "title": "Microclimate model x UBEM/BEM engine",
        "fields": ["microclimate_model", "ubem_tool", "bem_engine"],
        "caption": "Figure 5. Tool map connecting microclimate models with UBEM tools and BEM engines. It supports a descriptive claim about toolchain combinations represented in the evidence matrix.",
    },
    "figure_6_research_gap_matrix": {
        "title": "Validation x uncertainty x policy application",
        "fields": ["validation_data", "uncertainty_method", "policy_application"],
        "caption": "Figure 6. Research gap matrix relating validation evidence, uncertainty methods, and policy applications. It supports identification of evidence gaps only where extracted records provide those fields.",
    },
}


def is_missing(value: str) -> bool:
    return value.strip() == "" or value.strip().lower() == NOT_REPORTED


def split_values(value: str) -> list[str]:
    if is_missing(value):
        return []
    parts = []
    for raw in value.replace("|", ";").split(";"):
        item = raw.strip()
        if item and item.lower() != NOT_REPORTED:
            parts.append(item)
    return parts


def values_for_fields(row: dict[str, str], fields: Iterable[str]) -> list[str]:
    values: list[str] = []
    for field in fields:
        values.extend(split_values(row.get(field, "")))
    return values


def missingness(rows: list[dict[str, str]], field: str) -> float | None:
    if not rows:
        return None
    missing = sum(1 for row in rows if is_missing(row.get(field, "")))
    return missing / len(rows)


def collect_warnings(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    warnings = []
    if not rows:
        warnings.append(
            {
                "figure": "all",
                "field": "all",
                "missing_percent": "not applicable",
                "warning": "No extracted records are available; evidence-based figures contain no substantive values.",
            }
        )
        return warnings
    for figure_id, spec in FIGURE_SPECS.items():
        for field in spec["fields"]:
            pct = missingness(rows, field)
            if pct is not None and pct > 0.30:
                warnings.append(
                    {
                        "figure": figure_id,
                        "field": field,
                        "missing_percent": f"{pct * 100:.1f}",
                        "warning": "More than 30% missing or not reported values.",
                    }
                )
    return warnings


def setup_matplotlib():
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.edgecolor": "#333333",
            "axes.labelcolor": "#222222",
            "xtick.color": "#222222",
            "ytick.color": "#222222",
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )
    return plt


def save_figure(fig, figures_dir: Path, figure_id: str) -> None:
    fig.savefig(figures_dir / f"{figure_id}.svg", format="svg", bbox_inches="tight")
    fig.savefig(figures_dir / f"{figure_id}.png", format="png", dpi=600, bbox_inches="tight")


def empty_figure(plt, title: str, note: str = "No extracted records available"):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.axis("off")
    ax.text(0.5, 0.56, title, ha="center", va="center", fontsize=14, weight="bold")
    ax.text(0.5, 0.43, note, ha="center", va="center", fontsize=11, color="#555555")
    return fig


def plot_prisma(plt, prisma_rows: list[dict[str, str]], figures_dir: Path) -> None:
    figure_id = "figure_1_prisma_flow"
    if not prisma_rows:
        fig = empty_figure(plt, "Figure 1. PRISMA flow diagram", "No PRISMA count table available")
        save_figure(fig, figures_dir, figure_id)
        plt.close(fig)
        return

    stages = ["identified", "deduplicated", "screened", "excluded", "full-text assessed", "included", "uncertain"]
    counts = {row.get("stage", ""): row.get("count", "0") for row in prisma_rows}
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    y_positions = [0.92, 0.78, 0.64, 0.50, 0.36, 0.22, 0.08]
    for index, (stage, y) in enumerate(zip(stages, y_positions)):
        label = f"{stage.title()}\n n = {counts.get(stage, '0')}"
        ax.text(
            0.5,
            y,
            label,
            ha="center",
            va="center",
            fontsize=11,
            bbox={"boxstyle": "round,pad=0.35", "fc": "#F7F7F7", "ec": "#333333", "lw": 1.0},
        )
        if index < len(stages) - 1:
            ax.annotate("", xy=(0.5, y_positions[index + 1] + 0.055), xytext=(0.5, y - 0.055), arrowprops={"arrowstyle": "->", "lw": 1.0, "color": "#333333"})
    ax.set_title("Figure 1. PRISMA flow diagram", fontsize=14, weight="bold")
    save_figure(fig, figures_dir, figure_id)
    plt.close(fig)


def plot_publication_trend(plt, rows: list[dict[str, str]], figures_dir: Path) -> None:
    figure_id = "figure_2_annual_publication_trend"
    counts = collections.Counter(row.get("year", "") for row in rows if not is_missing(row.get("year", "")))
    if not counts:
        fig = empty_figure(plt, "Figure 2. Annual publication trend")
        save_figure(fig, figures_dir, figure_id)
        plt.close(fig)
        return
    years = sorted(counts)
    values = [counts[year] for year in years]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(years, values, color="#4C78A8")
    ax.set_xlabel("Publication year")
    ax.set_ylabel("Number of studies")
    ax.set_title("Figure 2. Annual publication trend", fontsize=13, weight="bold")
    ax.tick_params(axis="x", rotation=45)
    save_figure(fig, figures_dir, figure_id)
    plt.close(fig)


def top_values(counter: collections.Counter[str], limit: int = 12) -> list[str]:
    return [value for value, _ in counter.most_common(limit)]


def heatmap_counts(rows: list[dict[str, str]], row_field: str, col_fields: list[str], max_items: int = 12):
    row_counter: collections.Counter[str] = collections.Counter()
    col_counter: collections.Counter[str] = collections.Counter()
    pair_counter: collections.Counter[tuple[str, str]] = collections.Counter()
    for row in rows:
        row_values = split_values(row.get(row_field, ""))
        col_values = values_for_fields(row, col_fields)
        row_counter.update(row_values)
        col_counter.update(col_values)
        for row_value in row_values:
            for col_value in col_values:
                pair_counter[(row_value, col_value)] += 1
    y_labels = top_values(row_counter, max_items)
    x_labels = top_values(col_counter, max_items)
    matrix = [[pair_counter[(y, x)] for x in x_labels] for y in y_labels]
    return x_labels, y_labels, matrix


def draw_heatmap(plt, x_labels: list[str], y_labels: list[str], matrix: list[list[int]], title: str, figure_id: str, figures_dir: Path) -> None:
    if not x_labels or not y_labels:
        fig = empty_figure(plt, title)
        save_figure(fig, figures_dir, figure_id)
        plt.close(fig)
        return
    fig_w = max(7, min(12, 0.45 * len(x_labels) + 4))
    fig_h = max(5, min(10, 0.38 * len(y_labels) + 3))
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    image = ax.imshow(matrix, cmap="Blues", aspect="auto")
    ax.set_xticks(range(len(x_labels)))
    ax.set_xticklabels(x_labels, rotation=45, ha="right")
    ax.set_yticks(range(len(y_labels)))
    ax.set_yticklabels(y_labels)
    ax.set_title(title, fontsize=13, weight="bold")
    for y_index, row in enumerate(matrix):
        for x_index, value in enumerate(row):
            if value:
                ax.text(x_index, y_index, str(value), ha="center", va="center", fontsize=8)
    fig.colorbar(image, ax=ax, label="Record count")
    save_figure(fig, figures_dir, figure_id)
    plt.close(fig)


def plot_variable_output_heatmap(plt, rows: list[dict[str, str]], figures_dir: Path) -> None:
    figure_id = "figure_3_microclimate_variable_by_ubem_output_heatmap"
    x_labels, y_labels, matrix = heatmap_counts(rows, "microclimate_variable", ["energy_output", "comfort_output", "carbon_output"])
    draw_heatmap(plt, x_labels, y_labels, matrix, "Figure 3. Microclimate variable x UBEM output", figure_id, figures_dir)


def plot_tool_map(plt, rows: list[dict[str, str]], figures_dir: Path) -> None:
    figure_id = "figure_5_tool_map"
    x_labels, y_labels, matrix = heatmap_counts(rows, "microclimate_model", ["ubem_tool", "bem_engine"])
    draw_heatmap(plt, x_labels, y_labels, matrix, "Figure 5. Microclimate model x UBEM/BEM engine", figure_id, figures_dir)


def sankey_flows(rows: list[dict[str, str]]):
    left_mid: collections.Counter[tuple[str, str]] = collections.Counter()
    mid_right: collections.Counter[tuple[str, str]] = collections.Counter()
    node_counts = {"left": collections.Counter(), "middle": collections.Counter(), "right": collections.Counter()}
    for row in rows:
        left_values = split_values(row.get("microclimate_data_source", ""))
        mid_values = split_values(row.get("coupling_strategy", ""))
        right_values = split_values(row.get("energy_output", ""))
        for value in left_values:
            node_counts["left"][value] += 1
        for value in mid_values:
            node_counts["middle"][value] += 1
        for value in right_values:
            node_counts["right"][value] += 1
        for left in left_values:
            for middle in mid_values:
                left_mid[(left, middle)] += 1
        for middle in mid_values:
            for right in right_values:
                mid_right[(middle, right)] += 1
    return node_counts, left_mid, mid_right


def plot_sankey(plt, rows: list[dict[str, str]], figures_dir: Path) -> None:
    from matplotlib.path import Path as MplPath
    from matplotlib.patches import PathPatch

    figure_id = "figure_4_data_source_coupling_energy_output_sankey"
    node_counts, left_mid, mid_right = sankey_flows(rows)
    if not left_mid and not mid_right:
        fig = empty_figure(plt, "Figure 4. Data source -> coupling strategy -> energy output")
        save_figure(fig, figures_dir, figure_id)
        plt.close(fig)
        return

    columns = {
        "left": top_values(node_counts["left"], 8),
        "middle": top_values(node_counts["middle"], 8),
        "right": top_values(node_counts["right"], 8),
    }
    x_pos = {"left": 0.08, "middle": 0.50, "right": 0.92}
    y_pos: dict[tuple[str, str], float] = {}
    for column, labels in columns.items():
        step = 1 / (len(labels) + 1)
        for index, label in enumerate(labels, start=1):
            y_pos[(column, label)] = 1 - step * index

    fig, ax = plt.subplots(figsize=(11, 6))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    max_flow = max(list(left_mid.values()) + list(mid_right.values()) or [1])

    def draw_curve(start_col: str, start: str, end_col: str, end: str, count: int) -> None:
        if (start_col, start) not in y_pos or (end_col, end) not in y_pos:
            return
        x0, y0 = x_pos[start_col], y_pos[(start_col, start)]
        x1, y1 = x_pos[end_col], y_pos[(end_col, end)]
        control = (x1 - x0) * 0.5
        path = MplPath(
            [(x0, y0), (x0 + control, y0), (x1 - control, y1), (x1, y1)],
            [MplPath.MOVETO, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4],
        )
        width = 0.5 + 5.0 * count / max_flow
        ax.add_patch(PathPatch(path, facecolor="none", edgecolor="#4C78A8", lw=width, alpha=0.35))

    for (left, middle), count in left_mid.items():
        draw_curve("left", left, "middle", middle, count)
    for (middle, right), count in mid_right.items():
        draw_curve("middle", middle, "right", right, count)

    headings = {"left": "Data source", "middle": "Coupling strategy", "right": "Energy output"}
    for column, labels in columns.items():
        ax.text(x_pos[column], 0.98, headings[column], ha="center", va="top", fontsize=11, weight="bold")
        for label in labels:
            ax.text(
                x_pos[column],
                y_pos[(column, label)],
                label,
                ha="center",
                va="center",
                fontsize=9,
                bbox={"boxstyle": "round,pad=0.22", "fc": "#F7F7F7", "ec": "#333333", "lw": 0.8},
            )
    ax.set_title("Figure 4. Data source -> coupling strategy -> energy output", fontsize=13, weight="bold")
    save_figure(fig, figures_dir, figure_id)
    plt.close(fig)


def plot_gap_matrix(plt, rows: list[dict[str, str]], figures_dir: Path) -> None:
    figure_id = "figure_6_research_gap_matrix"
    validation_counter: collections.Counter[str] = collections.Counter()
    uncertainty_counter: collections.Counter[str] = collections.Counter()
    pair_counter: collections.Counter[tuple[str, str]] = collections.Counter()
    policy_counter: collections.Counter[tuple[str, str]] = collections.Counter()
    for row in rows:
        validations = split_values(row.get("validation_data", ""))
        uncertainties = split_values(row.get("uncertainty_method", ""))
        policies = split_values(row.get("policy_application", ""))
        validation_counter.update(validations)
        uncertainty_counter.update(uncertainties)
        for validation in validations:
            for uncertainty in uncertainties:
                pair_counter[(validation, uncertainty)] += 1
                if policies:
                    policy_counter[(validation, uncertainty)] += 1

    y_labels = top_values(validation_counter, 10)
    x_labels = top_values(uncertainty_counter, 10)
    if not x_labels or not y_labels:
        fig = empty_figure(plt, "Figure 6. Validation x uncertainty x policy application")
        save_figure(fig, figures_dir, figure_id)
        plt.close(fig)
        return

    fig, ax = plt.subplots(figsize=(9, 6))
    for y_index, validation in enumerate(y_labels):
        for x_index, uncertainty in enumerate(x_labels):
            count = pair_counter[(validation, uncertainty)]
            if count:
                policy_count = policy_counter[(validation, uncertainty)]
                size = 120 + 260 * math.sqrt(count)
                color = "#4C78A8" if policy_count else "#BAB0AC"
                ax.scatter(x_index, y_index, s=size, color=color, alpha=0.75, edgecolors="#333333", linewidths=0.5)
                ax.text(x_index, y_index, str(count), ha="center", va="center", fontsize=8)
    ax.set_xticks(range(len(x_labels)))
    ax.set_xticklabels(x_labels, rotation=45, ha="right")
    ax.set_yticks(range(len(y_labels)))
    ax.set_yticklabels(y_labels)
    ax.set_xlabel("Uncertainty method")
    ax.set_ylabel("Validation data")
    ax.set_title("Figure 6. Validation x uncertainty x policy application", fontsize=13, weight="bold")
    ax.grid(True, linestyle=":", color="#DDDDDD")
    save_figure(fig, figures_dir, figure_id)
    plt.close(fig)


def write_warnings(figures_dir: Path, warnings: list[dict[str, str]]) -> None:
    csv_path = figures_dir / "figure_missingness_warnings.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["figure", "field", "missing_percent", "warning"])
        writer.writeheader()
        writer.writerows(warnings)

    md_lines = ["# Figure Missingness Warnings", ""]
    if not warnings:
        md_lines.append("No figure field exceeds 30% missingness.")
    else:
        for warning in warnings:
            missing_percent = warning["missing_percent"]
            suffix = "%" if missing_percent.replace(".", "", 1).isdigit() else ""
            md_lines.append(
                f"- `{warning['figure']}` / `{warning['field']}`: {missing_percent}{suffix} - {warning['warning']}"
            )
    md_lines.append("")
    (figures_dir / "figure_missingness_warnings.md").write_text("\n".join(md_lines), encoding="utf-8")


def write_captions(figures_dir: Path, rows: list[dict[str, str]], warnings: list[dict[str, str]]) -> None:
    warning_by_figure: dict[str, list[str]] = collections.defaultdict(list)
    for warning in warnings:
        warning_by_figure[warning["figure"]].append(f"{warning['field']} missingness: {warning['missing_percent']}")

    lines = ["# Figure Captions", ""]
    for figure_id, spec in FIGURE_SPECS.items():
        lines.append(f"## {figure_id}")
        lines.append("")
        lines.append(spec["caption"])
        if not rows and figure_id != "figure_1_prisma_flow":
            lines.append("Current evidence status: no extracted records are available, so this figure supports no substantive literature claim yet.")
        elif warning_by_figure.get(figure_id):
            lines.append("Missingness warning: " + "; ".join(warning_by_figure[figure_id]) + ".")
        lines.append("")
    (figures_dir / "figure_captions.md").write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", default="data/processed/evidence_matrix.csv")
    parser.add_argument("--prisma", default="data/processed/prisma_counts.csv")
    parser.add_argument("--figures-dir", default="manuscript/figures")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    evidence_path = Path(args.evidence)
    prisma_path = Path(args.prisma)
    figures_dir = Path(args.figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)

    rows = read_csv(evidence_path) if evidence_path.exists() else []
    prisma_rows = read_csv(prisma_path) if prisma_path.exists() else []
    plt = setup_matplotlib()

    plot_prisma(plt, prisma_rows, figures_dir)
    plot_publication_trend(plt, rows, figures_dir)
    plot_variable_output_heatmap(plt, rows, figures_dir)
    plot_sankey(plt, rows, figures_dir)
    plot_tool_map(plt, rows, figures_dir)
    plot_gap_matrix(plt, rows, figures_dir)

    warnings = collect_warnings(rows)
    write_warnings(figures_dir, warnings)
    write_captions(figures_dir, rows, warnings)
    print(f"Wrote review figures to {figures_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
