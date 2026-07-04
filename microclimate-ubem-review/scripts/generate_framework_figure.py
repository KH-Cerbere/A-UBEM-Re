"""Generate the four-layer microclimate-aware UBEM conceptual framework figure."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path
from textwrap import dedent


LAYERS = [
    (
        "Microclimate data layer",
        [
            "Standard EPW / TMY",
            "Urban weather station",
            "Fixed sensor network",
            "Mobile measurement",
            "Remote sensing",
            "Reanalysis data",
            "CFD / ENVI-met / WRF / UWG",
            "Hybrid observational-simulation data",
        ],
    ),
    (
        "Transformation and coupling layer",
        [
            "Weather file replacement",
            "Weather morphing",
            "UWG-based transformation",
            "UCM -> UBEM",
            "UBEM -> UCM",
            "Two-way coupling / co-simulation",
            "Surrogate microclimate modeling",
            "Data assimilation",
        ],
    ),
    (
        "UBEM impact layer",
        [
            "Cooling demand",
            "Heating demand",
            "Peak load",
            "Thermal comfort",
            "Overheating risk",
            "Retrofit performance",
            "Carbon emissions",
            "Grid interaction",
        ],
    ),
    (
        "Policy-grade reliability layer",
        [
            "Validation",
            "Calibration",
            "Uncertainty propagation",
            "Transferability",
            "Computational scalability",
            "Data standardization",
            "Decision usefulness",
        ],
    ),
]


def dot_label(title: str, items: list[str]) -> str:
    escaped = [item.replace("&", "and").replace('"', "'") for item in items]
    return title + "\\n" + "\\n".join(f"- {item}" for item in escaped)


def build_dot() -> str:
    nodes = []
    edges = []
    for index, (title, items) in enumerate(LAYERS, start=1):
        nodes.append(f'  L{index} [label="{dot_label(title, items)}"];')
        if index > 1:
            edges.append(f"  L{index - 1} -> L{index};")
    return dedent(
        f"""
        digraph MicroclimateUBEMFramework {{
          graph [rankdir=LR, bgcolor="white", pad="0.2", nodesep="0.45", ranksep="0.65"];
          node [shape=box, style="rounded,filled", fillcolor="#F7F7F7", color="#333333", penwidth=1.2,
                fontname="Arial", fontsize=12, margin="0.14,0.10"];
          edge [color="#333333", penwidth=1.4, arrowsize=0.8];
        {chr(10).join(nodes)}
        {chr(10).join(edges)}
        }}
        """
    ).strip() + "\n"


def build_mermaid() -> str:
    lines = ["flowchart LR"]
    for index, (title, items) in enumerate(LAYERS, start=1):
        label = title + "<br/>" + "<br/>".join(items)
        lines.append(f'  L{index}["{label}"]')
        if index > 1:
            lines.append(f"  L{index - 1} --> L{index}")
    return "\n".join(lines) + "\n"


def render_with_graphviz(dot_path: Path, svg_path: Path, png_path: Path) -> bool:
    dot = shutil.which("dot")
    if not dot:
        return False
    subprocess.run([dot, "-Tsvg", str(dot_path), "-o", str(svg_path)], check=True)
    subprocess.run([dot, "-Tpng", "-Gdpi=600", str(dot_path), "-o", str(png_path)], check=True)
    return True


def render_with_matplotlib(svg_path: Path, png_path: Path) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.set_xlim(0, 4)
    ax.set_ylim(0, 1)
    ax.axis("off")

    box_w = 0.86
    box_h = 0.78
    y = 0.11
    x_positions = [0.06, 1.06, 2.06, 3.06]

    for index, ((title, items), x) in enumerate(zip(LAYERS, x_positions), start=1):
        patch = FancyBboxPatch(
            (x, y),
            box_w,
            box_h,
            boxstyle="round,pad=0.025,rounding_size=0.025",
            linewidth=1.2,
            edgecolor="#333333",
            facecolor="#F7F7F7",
        )
        ax.add_patch(patch)
        ax.text(x + box_w / 2, y + box_h - 0.08, title, ha="center", va="top", fontsize=11, weight="bold")
        item_text = "\n".join(f"- {item}" for item in items)
        ax.text(x + 0.045, y + box_h - 0.17, item_text, ha="left", va="top", fontsize=8.7, linespacing=1.25)
        if index < len(LAYERS):
            arrow = FancyArrowPatch(
                (x + box_w + 0.02, y + box_h / 2),
                (x_positions[index] - 0.02, y + box_h / 2),
                arrowstyle="-|>",
                mutation_scale=14,
                linewidth=1.2,
                color="#333333",
            )
            ax.add_patch(arrow)

    fig.savefig(svg_path, format="svg", bbox_inches="tight")
    fig.savefig(png_path, format="png", dpi=600, bbox_inches="tight")
    plt.close(fig)


def write_caption(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "# Conceptual Framework Caption",
                "",
                "**Figure 0. Microclimate-aware UBEM conceptual framework.** The figure organizes the review into a left-to-right research pipeline from microclimate data sources, through transformation and coupling strategies, to UBEM impacts and policy-grade reliability criteria. It supports the conceptual claim that policy-grade microclimate-aware UBEM depends on traceable links between data, coupling, impact assessment, and reliability evidence.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--figures-dir", default="manuscript/figures")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    figures_dir = Path(args.figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)

    dot_path = figures_dir / "figure_0_conceptual_framework.dot"
    mermaid_path = figures_dir / "figure_0_conceptual_framework.mmd"
    svg_path = figures_dir / "figure_0_conceptual_framework.svg"
    png_path = figures_dir / "figure_0_conceptual_framework.png"
    caption_path = figures_dir / "figure_0_conceptual_framework_caption.md"

    dot_path.write_text(build_dot(), encoding="utf-8")
    mermaid_path.write_text(build_mermaid(), encoding="utf-8")
    rendered = render_with_graphviz(dot_path, svg_path, png_path)
    if not rendered:
        render_with_matplotlib(svg_path, png_path)
    write_caption(caption_path)
    print(f"Wrote conceptual framework to {svg_path} and {png_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
