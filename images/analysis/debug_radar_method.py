#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pandas", "matplotlib", "seaborn", "numpy"]
# ///

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("TkAgg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

sns.set_theme(style="whitegrid", rc={"axes.unicode_minus": False})

plt.rcParams.update(
    {
        "font.sans-serif": [
            "WenQuanYi Micro Hei",
            "WenQuanYi Zen Hei",
            "Noto Sans CJK SC",
            "Noto Sans CJK JP",
            "Noto Sans CJK",
            "Microsoft YaHei",
            "SimHei",
            "DejaVu Sans",
        ],
        "font.family": "sans-serif",
        "font.size": 10,
    }
)

matplotlib.rcParams.update(
    {
        "figure.dpi": 150,
        "savefig.dpi": 200,
        "figure.facecolor": "#FFFFFF",
        "axes.facecolor": "#FFFFFF",
        "axes.edgecolor": "#2A2A2A",
        "axes.linewidth": 1.1,
        "axes.labelcolor": "#1F1F1F",
        "axes.titlesize": 14,
        "axes.titleweight": "bold",
        "axes.grid": False,
        "grid.color": "#CFCFCF",
        "grid.linestyle": "--",
        "grid.linewidth": 0.6,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "xtick.color": "#1F1F1F",
        "ytick.color": "#1F1F1F",
        "legend.frameon": False,
        "legend.title_fontsize": 11,
    }
)

DATA_CSV = Path(__file__).with_name("analysis_summary_3d.csv")
EXPORTED_CSV = Path(__file__).with_name("radar_method_overall_debug_data.csv")
OUTPUT_PNG = Path(__file__).with_name("radar_method_overall_debug_preview.png")

COMPACT_RADAR_FIGSIZE = (6.4, 6.4)
COMPACT_RADAR_DIM_LABEL_SIZE = 13
COMPACT_RADAR_RING_LABEL_SIZE = 10
COMPACT_RADAR_LEGEND_SIZE = 13
DIMENSION_ORDER = ["有效性", "无干扰性", "可部署性"]


def display_label(name: str) -> str:
    if name == "all":
        return "KPEDefense"
    if name.startswith("no_"):
        suffix = name[3:].replace("_", " ")
        display_suffix = suffix.upper() if len(suffix) <= 4 else suffix.capitalize()
        return f"KPEDefense w/o {display_suffix}"
    return name.replace("_", " ")


def ordered_dimensions(dims: list[str]) -> list[str]:
    ordered = [dim for dim in DIMENSION_ORDER if dim in dims]
    remaining = [dim for dim in dims if dim not in ordered]
    return ordered + sorted(remaining)


def ensure_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for col in columns:
        if col in df.columns:
            df.loc[:, col] = pd.to_numeric(df[col], errors="coerce")
    return df


def transform_rank_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    if df.empty:
        return df
    for col in columns:
        if col in df.columns:
            df.loc[:, col] = pd.to_numeric(df[col], errors="coerce")
            df = df.astype({col: "float64"})
            series = df[col]
            max_rank = series.max()
            if pd.notna(max_rank) and max_rank > 1:
                df.loc[:, col] = (max_rank - series) / (max_rank - 1)
            else:
                df.loc[:, col] = 1.0
    return df


def weighted_avg_df(
    df: pd.DataFrame,
    group_cols: list[str],
    value_col: str = "avg_rank",
    weight_col: str = "count",
) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=[*group_cols, value_col])
    needed_cols = list(dict.fromkeys([*group_cols, value_col, weight_col]))
    data = df[needed_cols].copy()
    data["__num"] = data[value_col] * data[weight_col]
    grouped = data.groupby(group_cols, dropna=False).agg({"__num": "sum", weight_col: "sum"})
    grouped = grouped[grouped[weight_col] != 0]
    if grouped.empty:
        return pd.DataFrame(columns=[*group_cols, value_col])
    grouped[value_col] = grouped["__num"] / grouped[weight_col]
    grouped = grouped.drop(columns="__num").reset_index()
    return grouped[[*group_cols, value_col]]


def build_plot() -> tuple[plt.Figure, object, object]:
    csv3 = pd.read_csv(DATA_CSV)
    csv3 = transform_rank_columns(csv3, ["avg_rank", "min_rank", "max_rank"])

    dims = ordered_dimensions(sorted(csv3["dimension"].dropna().unique().tolist()))
    if not dims:
        raise ValueError("No dimensions found in analysis_summary_3d.csv")

    data = weighted_avg_df(csv3, ["method", "dimension"])
    data = ensure_numeric(data, ["avg_rank"])
    if data.empty:
        raise ValueError("No aggregated data available for method radar chart")

    export_df = data.copy()
    export_df.insert(1, "method_label", export_df["method"].map(display_label))
    export_df = export_df.sort_values(["method_label", "dimension"])
    export_df.to_csv(EXPORTED_CSV, index=False, encoding="utf-8-sig")

    pivot = data.pivot_table(index="method", columns="dimension", values="avg_rank", aggfunc="first")
    pivot = pivot.reindex(columns=dims)
    pivot = pivot.dropna(how="all")
    if pivot.empty:
        raise ValueError("Pivot table is empty for method radar chart")

    angles = np.linspace(0, 2 * np.pi, len(dims), endpoint=False).tolist()
    angles += angles[:1]

    label_positions = {
        "有效性": (0.50, 1.02),
        "无干扰性": (1.00, 0.22),
        "可部署性": (0.00, 0.22),
    }

    fig = plt.figure(figsize=COMPACT_RADAR_FIGSIZE)
    ax = fig.add_subplot(111, polar=True)
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    theta_deg = np.degrees(angles[:-1])
    ax.set_thetagrids(theta_deg, ["" for _ in dims], fontsize=COMPACT_RADAR_DIM_LABEL_SIZE)
    for label, (x, y) in label_positions.items():
        ax.text(
            x,
            y,
            label,
            transform=ax.transAxes,
            ha="center",
            va="center",
            fontsize=COMPACT_RADAR_DIM_LABEL_SIZE,
        )

    ax.set_ylim(0, 0.7)
    ax.set_yticks([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7])
    ax.set_yticklabels(
        ["0.1", "0.2", "0.3", "0.4", "0.5", "0.6", "0.7"],
        fontsize=COMPACT_RADAR_RING_LABEL_SIZE,
    )
    ax.grid(color="#D0D0D0", linestyle="--", linewidth=0.6, alpha=0.9)

    palette = sns.color_palette("husl", n_colors=len(pivot.index))
    for name, color in zip(pivot.index.tolist(), palette):
        values = pivot.loc[name].to_numpy(dtype=float)
        if np.all(np.isnan(values)):
            continue
        mean_val = np.nanmean(values)
        if np.isnan(mean_val):
            mean_val = 0.0
        values = np.nan_to_num(values, nan=mean_val).tolist()
        values += values[:1]
        ax.plot(angles, values, color=color, linewidth=2.8, label=display_label(str(name)))
        ax.fill(angles, values, color=color, alpha=0.15)

    ax.set_title("")
    legend = ax.legend(
        loc="upper right",
        bbox_to_anchor=(1.24, 1.08),
        frameon=False,
        fontsize=COMPACT_RADAR_LEGEND_SIZE,
    )
    legend.set_draggable(True, use_blit=False, update="bbox")
    plt.tight_layout(pad=0.8)
    return fig, ax, legend


def main() -> None:
    fig, ax, legend = build_plot()

    def on_close(event) -> None:
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        legend_bbox = legend.get_window_extent(renderer=renderer)
        anchor_x, anchor_y = ax.transAxes.inverted().transform((legend_bbox.x1, legend_bbox.y1))
        print(f"Suggested bbox_to_anchor=({anchor_x:.3f}, {anchor_y:.3f})")
        fig.savefig(OUTPUT_PNG, dpi=200, bbox_inches="tight")
        print(f"Data exported to: {EXPORTED_CSV}")
        print(f"Preview saved to: {OUTPUT_PNG}")

    fig.canvas.mpl_connect("close_event", on_close)

    print(f"Data exported to: {EXPORTED_CSV}")
    print("Drag the legend with the mouse, then close the window.")
    print("The terminal will print the suggested bbox_to_anchor for plot.py.")
    plt.show()


if __name__ == "__main__":
    main()
