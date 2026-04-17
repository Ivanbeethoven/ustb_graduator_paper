#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import argparse

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

# Styling (match plot.py)
sns.set_theme(style="whitegrid", rc={"axes.unicode_minus": False})
matplotlib.rcParams.update({
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
})

COMPACT_RADAR_FIGSIZE = (6.4, 6.4)
COMPACT_RADAR_DIM_LABEL_SIZE = 13
COMPACT_RADAR_RING_LABEL_SIZE = 10
COMPACT_RADAR_TITLE_SIZE = 15
COMPACT_RADAR_LEGEND_SIZE = 11

_DIMENSION_ORDER = ["有效性", "无干扰性", "可部署性"]


def _ordered_dimensions(dims: list[str]) -> list[str]:
    ordered = [d for d in _DIMENSION_ORDER if d in dims]
    remaining = [d for d in dims if d not in ordered]
    return ordered + sorted(remaining)


def _ensure_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for col in columns:
        if col in df.columns:
            df.loc[:, col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _transform_rank_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
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


def weighted_avg_df(df: pd.DataFrame, group_cols: list[str], value_col: str = "avg_rank", weight_col: str = "count") -> pd.DataFrame:
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


def plot_radar_for_judge(csv3: pd.DataFrame, out_dir: Path, judge_key: str, label: str) -> None:
    plots_dir = out_dir / "plots" / "summary"
    plots_dir.mkdir(parents=True, exist_ok=True)

    judge_df = csv3[csv3["judge"] == judge_key]
    if judge_df.empty:
        raise ValueError(f"No rows for judge={judge_key}")

    dims = _ordered_dimensions(sorted(judge_df["dimension"].dropna().unique().tolist()))
    if not dims:
        raise ValueError("No dimensions found")

    angles = np.linspace(0, 2 * np.pi, len(dims), endpoint=False).tolist()
    angles += angles[:1]

    def _plot(entity_col: str, title: str, filename: str, label_positions: dict[str, tuple[float, float]]) -> None:
        data = weighted_avg_df(judge_df, [entity_col, "dimension"])
        if data.empty:
            return
        data = _ensure_numeric(data, ["avg_rank"])
        pivot = data.pivot_table(index=entity_col, columns="dimension", values="avg_rank", aggfunc="first")
        if pivot.empty:
            return
        pivot = pivot.reindex(columns=dims)
        pivot = pivot.dropna(how="all")
        if pivot.empty:
            return

        palette = sns.color_palette("husl", n_colors=len(pivot.index))

        fig = plt.figure(figsize=COMPACT_RADAR_FIGSIZE)
        ax = fig.add_subplot(111, polar=True)
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)
        theta_deg = np.degrees(angles[:-1])
        ax.set_thetagrids(theta_deg, [""] * len(dims), fontsize=COMPACT_RADAR_DIM_LABEL_SIZE)
        for lbl, (x, y) in label_positions.items():
            ax.text(
                x,
                y,
                lbl,
                transform=ax.transAxes,
                ha="center",
                va="center",
                fontsize=COMPACT_RADAR_DIM_LABEL_SIZE,
            )
        ax.set_ylim(0, 1.0)
        ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
        ax.set_yticklabels(
            ["0.2", "0.4", "0.6", "0.8", "1.0"],
            fontsize=COMPACT_RADAR_RING_LABEL_SIZE,
        )
        ax.grid(color="#D0D0D0", linestyle="--", linewidth=0.6, alpha=0.9)

        for (name, color) in zip(pivot.index.tolist(), palette):
            values = pivot.loc[name].to_numpy(dtype=float)
            if np.all(np.isnan(values)):
                continue
            mean_val = np.nanmean(values)
            if np.isnan(mean_val):
                mean_val = 0.0
            values = np.nan_to_num(values, nan=mean_val).tolist()
            values += values[:1]
            ax.plot(angles, values, color=color, linewidth=2.8, label=str(name))
            ax.fill(angles, values, color=color, alpha=0.15)

            ax.set_title("")
        ax.legend(
            loc="upper right",
            bbox_to_anchor=(1.24, 1.08),
            frameon=False,
            fontsize=COMPACT_RADAR_LEGEND_SIZE,
        )
        plt.tight_layout(pad=0.8)
        plt.savefig(plots_dir / filename, dpi=200, bbox_inches="tight")
        plt.close()

    generator_label_positions = {
        "有效性": (0.50, 1.02),
        "无干扰性": (1.00, 0.22),
        "可部署性": (0.00, 0.22),
    }
    method_label_positions = {
        "有效性": (0.50, 1.02),
        "无干扰性": (1.00, 0.22),
        "可部署性": (0.00, 0.22),
    }

    _plot(
        "generator",
        f"生成模型三维度雷达图｜评审者：{label}",
        f"radar_generator_{judge_key}.png",
        generator_label_positions,
    )
    _plot(
        "method",
        f"方法配置三维度雷达图｜评审者：{label}",
        f"radar_method_{judge_key}.png",
        method_label_positions,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--out-dir", type=Path, default=Path.cwd() / "analysis")
    p.add_argument("--judge", type=str, default="gpt5")
    p.add_argument("--label", type=str, default="GPT-5")
    args = p.parse_args()

    csv3 = pd.read_csv(args.out_dir / "analysis_summary_3d.csv")
    csv3 = _transform_rank_columns(csv3, ["avg_rank", "min_rank", "max_rank"])
    plot_radar_for_judge(csv3, args.out_dir, args.judge, args.label)
