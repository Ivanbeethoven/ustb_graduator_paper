#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional, Literal, cast, Any

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")  # Use non-GUI backend for reliable font rendering (incl. Chinese)
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.container import BarContainer
import seaborn as sns

# Global styling: rely on matplotlibrc for fonts, use a clean seaborn theme
sns.set_theme(style="whitegrid", rc={"axes.unicode_minus": False})

# Ensure Chinese-capable fonts are preferred at runtime to avoid missing-glyph warnings.
# This complements the user's matplotlibrc; put common CJK fonts first so matplotlib
# will try them before falling back to DejaVu Sans.
import matplotlib.pyplot as _plt_for_rc
_plt_for_rc.rcParams.update({
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


def _apply_origin_style() -> None:
    """Approximate OriginLab's clean plotting aesthetics via rcParams."""
    matplotlib.rcParams.update({
        # higher DPI for crisper exported images
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
    })


_apply_origin_style()


def _display_label(name: str) -> str:
    """Return a human-friendly display label (e.g. map 'no_rag' -> 'KPEDefense w/o RAG')."""
    if name is None:
        return ""
    s = str(name)
    # 'all' -> 'KPEDefense' (complete method)
    if s == "all":
        return "KPEDefense"
    # 'no_rag' -> 'KPEDefense w/o RAG', 'no_cot' -> 'KPEDefense w/o COT', etc.
    if s.startswith("no_"):
        suffix = s[3:].replace("_", " ")
        # short abbreviations (≤4 chars) in uppercase, longer words capitalized
        display_suffix = suffix.upper() if len(suffix) <= 4 else suffix.capitalize()
        return "KPEDefense w/o " + display_suffix
    # fallback
    return s.replace("_", " ")


def _safe_name(name: str) -> str:
    """Return a filesystem-safe name derived from the display label.

    Replaces path-separators and spaces with underscores so labels like
    'w/o RAG' won't be interpreted as directories when used in file paths.
    """
    disp = _display_label(name)
    # replace slashes and spaces with underscore
    return disp.replace("/", "_").replace(" ", "_")


_COMPACT_JUDGE_SUMMARY_FIGSIZE = (8.4, 4.9)
_COMPACT_JUDGE_SUMMARY_TITLE_SIZE = 15
_COMPACT_JUDGE_SUMMARY_LABEL_SIZE = 13
_COMPACT_JUDGE_SUMMARY_TICK_SIZE = 11
_COMPACT_JUDGE_SUMMARY_BAR_LABEL_SIZE = 10
_COMPACT_JUDGE_SUMMARY_LEGEND_SIZE = 13

_COMPACT_HEATMAP_FIGSIZE = (6.2, 5.5)
_COMPACT_HEATMAP_TITLE_SIZE = 15
_COMPACT_HEATMAP_LABEL_SIZE = 13
_COMPACT_HEATMAP_TICK_SIZE = 11
_COMPACT_HEATMAP_ANNOT_SIZE = 11

_COMPACT_RADAR_FIGSIZE = (6.4, 6.4)
_COMPACT_RADAR_DIM_LABEL_SIZE = 13
_COMPACT_RADAR_RING_LABEL_SIZE = 10
_COMPACT_RADAR_TITLE_SIZE = 15
_COMPACT_RADAR_LEGEND_SIZE = 13


_BAR_COLORS = [
    "#1C1C1C",
    "#4F4F4F",
    "#7A7A7A",
    "#A5A5A5",
    "#CFCFCF",
]

_MONO_COLORS = [
    "#1C1C1C",
    "#4F4F4F",
    "#7A7A7A",
    "#A5A5A5",
    "#CFCFCF",
]

_HEATMAP_CMAP = sns.color_palette("Greys", as_cmap=True)

_DIMENSION_ORDER = ["有效性", "无干扰性", "可部署性"]


def _bar_palette(count: int, monochrome: bool = False) -> list[str]:
    base = _MONO_COLORS if monochrome else _BAR_COLORS
    if count <= 1:
        return [base[0]]
    if count <= len(base):
        return base[:count]
    repeats = (count // len(base)) + 1
    palette = (base * repeats)[:count]
    return palette


def _style_axes(ax: Axes, grid_axis: Literal["x", "y", "both"] | None = "y") -> None:
    spine_color = "#2A2A2A"
    ax.set_axisbelow(True)
    for spine_name, spine in ax.spines.items():
        if spine_name in {"top", "right"}:
            spine.set_visible(False)
        else:
            spine.set_color(spine_color)
            spine.set_linewidth(0.8)
    ax.tick_params(axis="both", colors="#1F1F1F", labelsize=11, width=1, length=4)
    if grid_axis:
        ax.grid(axis=grid_axis, color="#D0D0D0", linestyle="--", linewidth=0.6, alpha=0.9)
    else:
        ax.grid(False)


def _style_colorbar(ax: Axes, label: str | None = None) -> None:
    """Apply consistent styling to seaborn/matplotlib heatmap colorbars."""
    try:
        if not ax.collections:
            return
        colorbar = ax.collections[0].colorbar
        if colorbar is None:
            return
        colorbar.ax.tick_params(labelsize=10, width=0.8, length=3, colors="#1F1F1F")
        if label:
            colorbar.set_label(label, fontsize=11, color="#1F1F1F", rotation=90, labelpad=10)
    except Exception:
        return


def _ordered_dimensions(dims: list[str]) -> list[str]:
    ordered = [d for d in _DIMENSION_ORDER if d in dims]
    remaining = [d for d in dims if d not in ordered]
    return ordered + sorted(remaining)


def _accentuate_bars(ax: Axes) -> None:
    """Give bars a subtle outline similar to Origin's defaults."""
    for patch in ax.patches:
        patch.set_edgecolor("#1F1F1F")
        patch.set_linewidth(0.6)


def _add_y_axis_arrow(ax: Axes) -> None:
    """Add an upward arrow to the y-axis to emphasize higher is better."""
    # Make y-axis spine visible with arrow style
    ax.spines['left'].set_visible(True)
    # Use FancyArrowPatch style for the left spine (y-axis)
    from matplotlib.patches import FancyArrowPatch
    ylim = ax.get_ylim()
    xlim = ax.get_xlim()
    x_pos = xlim[0]
    
    # Create an arrow that replaces the y-axis spine
    arrow = FancyArrowPatch(
        (x_pos, ylim[0]), (x_pos, ylim[1]),
        arrowstyle='-|>',
        mutation_scale=15,
        linewidth=0.8,
        color='#2A2A2A',
        clip_on=False,
        zorder=10
    )
    ax.add_patch(arrow)
    # Hide the original left spine since we replaced it with an arrow
    ax.spines['left'].set_visible(False)


def _title(head: str, dimension: str | None = None, extras: list[str] | None = None) -> str:
    parts = [head]
    if extras:
        parts.extend(extras)
    if dimension:
        parts.append(f"维度：{dimension}")
    return "｜".join(parts)


def load_csvs(in_dir: Path):
    overall = pd.read_csv(in_dir / "analysis_summary.csv")
    by_judge = pd.read_csv(in_dir / "analysis_summary_by_judge.csv")
    csv3 = pd.read_csv(in_dir / "analysis_summary_3d.csv")
    overall = _transform_rank_columns(overall, ["avg_rank", "min_rank", "max_rank"])
    by_judge = _transform_rank_columns(by_judge, ["avg_rank", "min_rank", "max_rank"])
    csv3 = _transform_rank_columns(csv3, ["avg_rank", "min_rank", "max_rank"])
    return overall, by_judge, csv3


def _apply_y_padding(ax: Axes, values, pad_ratio: float = 0.1) -> None:
    """Add headroom to y-axis based on data range to avoid cramped labels."""
    try:
        if values is None:
            return
        vals = [v for v in values if v is not None and pd.notna(v)]
        if not vals:
            return
        vmax = max(vals)
        vmin = min(vals)
        if vmax is None or vmin is None:
            return
        span = vmax - vmin
        pad = max(span * pad_ratio, 0.05 if vmax > 0 else 0)
        ax.set_ylim(0, vmax + pad)
    except Exception:
        # Best-effort; ignore if values not numeric
        return


def _ensure_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Coerce selected DataFrame columns to numeric, ignoring errors."""
    for col in columns:
        if col in df.columns:
            df.loc[:, col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _transform_rank_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Transform rank-like columns into normalized scores in [0, 1].

    Uses formula: s = (n - r) / (n - 1), where:
    - r is the rank (smaller is better)
    - n is the maximum rank
    - Rank 1 (best) → score 1.0
    - Rank n (worst) → score 0.0
    
    After transformation, larger values indicate better performance.
    """
    if df.empty:
        return df
    for col in columns:
        if col in df.columns:
            # Convert to numeric then force column dtype to float to avoid dtype warnings
            df.loc[:, col] = pd.to_numeric(df[col], errors="coerce")
            df = df.astype({col: "float64"})
            # Find max rank for normalization
            series = df[col]
            max_rank = series.max()
            if pd.notna(max_rank) and max_rank > 1:
                # Apply formula: s = (n - r) / (n - 1)
                df.loc[:, col] = (max_rank - series) / (max_rank - 1)
            else:
                # Edge case: only one item or all NaN
                df.loc[:, col] = 1.0
    return df


def plot_grouped_bar(csv3: pd.DataFrame, out_dir: Path, dimension: str):
    # grouped bar: x=method, hue=judge, y=avg_rank(排序得分) for a given generator profile
    base = out_dir / "plots" / dimension / "generator"
    base.mkdir(parents=True, exist_ok=True)
    df = csv3[csv3["dimension"] == dimension]
    for gen in sorted(df["generator"].unique()):
        sub = df[df["generator"] == gen]
        if sub.empty:
            continue
        pivot = sub.pivot_table(index="method", columns="judge", values="avg_rank", aggfunc="first")
        if pivot.empty:
            continue
        raw_methods = pivot.index.tolist()
        raw_judges = pivot.columns.tolist()
        display_methods = [_display_label(i) for i in raw_methods]
        display_judges = [_display_label(c) for c in raw_judges]
        pivot.index = display_methods
        pivot.columns = display_judges
        gen_dir = base / _safe_name(gen)
        gen_dir.mkdir(parents=True, exist_ok=True)
        palette = _bar_palette(max(len(pivot.columns), 1))
        ax = pivot.plot(kind="bar", figsize=(12, 5.2), color=palette)
        ax.set_title("")
        ax.set_ylabel("排序得分", fontsize=12)
        ax.set_xlabel("方法", fontsize=12)
        leg = ax.get_legend()
        if leg is not None:
            leg.set_title("")
        ax.tick_params(axis="x", labelrotation=0)
        for container in ax.containers:
            ax.bar_label(cast(BarContainer, container), fmt="{:.2f}", padding=2, fontsize=9)
        _apply_y_padding(ax, pivot.values.flatten())
        _style_axes(ax)
        _accentuate_bars(ax)
        plt.tight_layout()
        plt.savefig(gen_dir / f"grouped_bar_{_safe_name(gen)}_{dimension}.png", dpi=200)
        plt.close()


def plot_heatmap(csv3: pd.DataFrame, out_dir: Path, dimension: str):
    base = out_dir / "plots" / dimension / "heatmap"
    base.mkdir(parents=True, exist_ok=True)
    df = csv3[csv3["dimension"] == dimension]
    for gen in sorted(df["generator"].unique()):
        sub = df[df["generator"] == gen]
        pivot = sub.pivot_table(index="judge", columns="method", values="avg_rank")
        try:
            pivot.index = [_display_label(i) for i in pivot.index]
        except Exception:
            pass
        try:
            pivot.columns = [_display_label(c) for c in pivot.columns]
        except Exception:
            pass
        gen_dir = base / _safe_name(gen)
        gen_dir.mkdir(parents=True, exist_ok=True)
        plt.figure(figsize=(11, 5))
        ax = sns.heatmap(pivot, annot=True, fmt=".2f", cmap=_HEATMAP_CMAP, cbar_kws={"shrink": 0.8})
        ax.set_title("")
        ax.set_ylabel("评委模型", fontsize=12)
        ax.set_xlabel("方法", fontsize=12)
        ax.title.set_fontsize(_COMPACT_HEATMAP_TITLE_SIZE)
        ax.title.set_y(1.01)
        ax.xaxis.label.set_size(_COMPACT_HEATMAP_LABEL_SIZE)
        ax.yaxis.label.set_size(_COMPACT_HEATMAP_LABEL_SIZE)
        ax.tick_params(axis="both", labelsize=_COMPACT_HEATMAP_TICK_SIZE)
        _style_axes(ax, grid_axis=None)
        plt.tight_layout()
        plt.savefig(gen_dir / f"heatmap_{_safe_name(gen)}_{dimension}.png", dpi=200)
        plt.close()


def weighted_avg(df: pd.DataFrame, value_col: str = "avg_rank", weight_col: str = "count") -> Optional[float]:
    if df.empty:
        return None
    try:
        total_w = df[weight_col].sum()
        if total_w == 0:
            return None
        return (df[value_col] * df[weight_col]).sum() / total_w
    except Exception:
        return None


def weighted_avg_series(df: pd.DataFrame, group_col: str, value_col: str = "avg_rank", weight_col: str = "count") -> pd.Series:
    """Compute weighted average per group without using GroupBy.apply to avoid pandas FutureWarning."""
    if df.empty:
        return pd.Series(dtype=float)
    try:
        num = (df[value_col] * df[weight_col]).groupby(df[group_col]).sum()
        den = df[weight_col].groupby(df[group_col]).sum()
        res = num / den
        res = res.replace([np.inf, -np.inf], np.nan).dropna()
        return res.astype(float)
    except Exception:
        return pd.Series(dtype=float)


def weighted_avg_df(df: pd.DataFrame, group_cols: list[str], value_col: str = "avg_rank", weight_col: str = "count") -> pd.DataFrame:
    """Weighted-average aggregation for multiple grouping columns."""
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


def plot_per_method(csv3: pd.DataFrame, out_dir: Path, dimension: str):
    base = out_dir / "plots" / dimension / "method"
    base.mkdir(parents=True, exist_ok=True)
    df = csv3[csv3["dimension"] == dimension]
    for method in sorted(df["method"].unique()):
        sub = df[df["method"] == method]
        if sub.empty:
            continue
        method_dir = base / _safe_name(method)
        method_dir.mkdir(parents=True, exist_ok=True)
        pivot = sub.pivot_table(index="judge", columns="generator", values="avg_rank")
        try:
            pivot.columns = [_display_label(c) for c in pivot.columns]
        except Exception:
            pass
        plt.figure(figsize=(10.5, 4.8))
        ax = sns.heatmap(pivot, annot=True, fmt=".2f", cmap=_HEATMAP_CMAP, cbar_kws={"shrink": 0.8})
        ax.set_title("")
        ax.set_ylabel("评委模型", fontsize=12)
        ax.set_xlabel("生成模型", fontsize=12)
        _style_axes(ax, grid_axis=None)
        plt.tight_layout()
        plt.savefig(method_dir / f"heatmap_method_{_safe_name(method)}_{dimension}.png", dpi=200)
        plt.close()

        by_judge = weighted_avg_series(sub, "judge").dropna()
        try:
            by_judge.index = [_display_label(i) for i in by_judge.index]
        except Exception:
            pass
        if not by_judge.empty:
            palette = _bar_palette(len(by_judge), monochrome=True)
            ax = by_judge.plot(kind="bar", figsize=(4.6, 4.0), color=palette, width=0.45)
            ax.set_title("")
            ax.set_ylabel("加权平均得分", fontsize=12)
            ax.set_xlabel("评委模型", fontsize=12)
            ax.tick_params(axis="x", labelrotation=0)
            for container in ax.containers:
                ax.bar_label(cast(BarContainer, container), fmt="{:.2f}", fontsize=9, padding=2)
            _apply_y_padding(ax, by_judge.values)
            _style_axes(ax)
            _accentuate_bars(ax)
            _add_y_axis_arrow(ax)
            plt.tight_layout()
            plt.savefig(method_dir / f"method_bar_by_judge_{_safe_name(method)}_{dimension}.png", dpi=200)
            plt.close()

        by_gen = weighted_avg_series(sub, "generator").dropna()
        try:
            by_gen.index = [_display_label(i) for i in by_gen.index]
        except Exception:
            pass
        if not by_gen.empty:
            palette = _bar_palette(len(by_gen), monochrome=True)
            ax = by_gen.plot(kind="bar", figsize=(4.6, 4.0), color=palette, width=0.45)
            ax.set_title("")
            ax.set_ylabel("加权平均得分", fontsize=12)
            ax.set_xlabel("生成模型", fontsize=12)
            ax.tick_params(axis="x", labelrotation=0)
            for container in ax.containers:
                ax.bar_label(cast(BarContainer, container), fmt="{:.2f}", fontsize=9, padding=2)
            _apply_y_padding(ax, by_gen.values)
            _style_axes(ax)
            _accentuate_bars(ax)
            _add_y_axis_arrow(ax)
            plt.tight_layout()
            plt.savefig(method_dir / f"method_bar_by_generator_{_safe_name(method)}_{dimension}.png", dpi=200)
            plt.close()


def plot_per_generator(csv3: pd.DataFrame, out_dir: Path, dimension: str):
    base = out_dir / "plots" / dimension / "generator"
    base.mkdir(parents=True, exist_ok=True)
    df = csv3[csv3["dimension"] == dimension]
    for gen in sorted(df["generator"].unique()):
        sub = df[df["generator"] == gen]
        if sub.empty:
            continue
        gen_dir = base / _safe_name(gen)
        gen_dir.mkdir(parents=True, exist_ok=True)
        pivot = sub.pivot_table(index="judge", columns="method", values="avg_rank")
        try:
            pivot.columns = [_display_label(c) for c in pivot.columns]
        except Exception:
            pass
        plt.figure(figsize=(11.5, 5))
        ax = sns.heatmap(pivot, annot=True, fmt=".2f", cmap=_HEATMAP_CMAP, cbar_kws={"shrink": 0.8})
        ax.set_title("")
        ax.set_ylabel("评委模型", fontsize=12)
        ax.set_xlabel("方法", fontsize=12)
        _style_axes(ax, grid_axis=None)
        plt.tight_layout()
        plt.savefig(gen_dir / f"heatmap_generator_{_safe_name(gen)}_{dimension}.png", dpi=200)
        plt.close()

        by_method = weighted_avg_series(sub, "method").dropna()
        try:
            by_method.index = [_display_label(i) for i in by_method.index]
        except Exception:
            pass
        if not by_method.empty:
            palette = _bar_palette(len(by_method), monochrome=True)
            ax = by_method.plot(kind="bar", figsize=(4.7, 4.0), color=palette, width=0.42)
            ax.set_title("")
            ax.set_ylabel("加权平均得分", fontsize=12)
            ax.set_xlabel("方法", fontsize=12)
            ax.tick_params(axis="x", labelrotation=0)
            for container in ax.containers:
                ax.bar_label(cast(BarContainer, container), fmt="{:.2f}", fontsize=9, padding=2)
            _apply_y_padding(ax, by_method.values)
            _style_axes(ax)
            _accentuate_bars(ax)
            _add_y_axis_arrow(ax)
            plt.tight_layout()
            plt.savefig(gen_dir / f"generator_bar_by_method_{_safe_name(gen)}_{dimension}.png", dpi=200)
            plt.close()

        by_judge = weighted_avg_series(sub, "judge").dropna()
        try:
            by_judge.index = [_display_label(i) for i in by_judge.index]
        except Exception:
            pass
        if not by_judge.empty:
            palette = _bar_palette(len(by_judge), monochrome=True)
            ax = by_judge.plot(kind="bar", figsize=(4.6, 4.0), color=palette, width=0.45)
            ax.set_title("")
            ax.set_ylabel("加权平均得分", fontsize=12)
            ax.set_xlabel("评委模型", fontsize=12)
            ax.tick_params(axis="x", labelrotation=0)
            for container in ax.containers:
                ax.bar_label(cast(BarContainer, container), fmt="{:.2f}", fontsize=9, padding=2)
            _apply_y_padding(ax, by_judge.values)
            _style_axes(ax)
            _accentuate_bars(ax)
            _add_y_axis_arrow(ax)
            plt.tight_layout()
            plt.savefig(gen_dir / f"generator_bar_by_judge_{_safe_name(gen)}_{dimension}.png", dpi=200)
            plt.close()


def plot_single_dimension(out_dir: Path, dimension: str, in_dir: Optional[Path] = None):
    """Single-dimension summary plots using per-dimension CSVs."""
    src = in_dir if in_dir is not None else out_dir
    plots_dir = out_dir / "plots" / dimension / "summary"
    plots_dir.mkdir(parents=True, exist_ok=True)
    dim_csv = src / f"analysis_summary_{dimension}.csv"
    judge_dim_csv = src / f"analysis_summary_by_judge_{dimension}.csv"
    if not dim_csv.exists():
        return
    df = pd.read_csv(dim_csv)
    df = _transform_rank_columns(df, ["avg_rank", "min_rank", "max_rank"])
    methods = df[df['type'] == 'method'].copy()
    methods = methods.sort_values('avg_rank', ascending=False)
    methods = _ensure_numeric(methods, ["avg_rank"])
    plt.figure(figsize=(5.2, 4.2))
    keys = [_display_label(k) for k in methods['key'].astype(str)]
    x = np.arange(len(keys))
    bars = plt.bar(x, methods['avg_rank'].astype(float), width=0.60, color=_bar_palette(len(keys), monochrome=True))
    plt.xticks(x, keys, rotation=0, ha='center', fontsize=10)
    plt.ylabel('排序得分', fontsize=12)
    plt.xlabel('方法', fontsize=12)
    plt.title(_title("方法汇总：排序得分", dimension), fontsize=14, pad=12)
    ax = plt.gca()
    ax.bar_label(bars, fmt="{:.2f}", fontsize=9, padding=2)
    _apply_y_padding(ax, methods['avg_rank'].to_numpy(dtype=float))
    _style_axes(ax)
    _accentuate_bars(ax)
    _add_y_axis_arrow(ax)
    plt.tight_layout()
    plt.savefig(plots_dir / f'single_dim_method_avg_{dimension}.png', dpi=200)
    plt.close()

    profiles = df[df['type'] == 'profile'].copy()
    profiles = profiles.sort_values('avg_rank', ascending=False)
    profiles = _ensure_numeric(profiles, ["avg_rank"])
    plt.figure(figsize=(5.2, 4.2))
    pkeys = [_display_label(k) for k in profiles['key'].astype(str)]
    x = np.arange(len(pkeys))
    bars = plt.bar(x, profiles['avg_rank'].astype(float), width=0.60, color=_bar_palette(len(pkeys), monochrome=True))
    plt.xticks(x, pkeys, rotation=0, ha='center', fontsize=10)
    plt.ylabel('排序得分', fontsize=12)
    plt.xlabel('生成模型', fontsize=12)
    plt.title(_title("生成模型汇总：排序得分", dimension), fontsize=14, pad=12)
    ax = plt.gca()
    ax.bar_label(bars, fmt="{:.2f}", fontsize=9, padding=2)
    _apply_y_padding(ax, profiles['avg_rank'].to_numpy(dtype=float))
    _style_axes(ax)
    _accentuate_bars(ax)
    _add_y_axis_arrow(ax)
    plt.tight_layout()
    plt.savefig(plots_dir / f'single_dim_profile_avg_{dimension}.png', dpi=200)
    plt.close()

    if judge_dim_csv.exists():
        jdf = pd.read_csv(judge_dim_csv)
        jdf = _transform_rank_columns(jdf, ["avg_rank", "min_rank", "max_rank"])
        jmethod = jdf[jdf['type'] == 'method']
        if not jmethod.empty:
            jmethod = _ensure_numeric(jmethod, ["avg_rank"])
            pivot = jmethod.pivot_table(
                index='key',
                columns='judge',
                values='avg_rank',
                aggfunc=lambda s: s.iloc[0] if len(s) else np.nan,
            )
            if pivot.empty:
                return
            raw_methods = pivot.index.tolist()
            raw_judges = pivot.columns.tolist()
            display_methods = [_display_label(i) for i in raw_methods]
            display_judges = [_display_label(j) for j in raw_judges]
            pivot.index = display_methods
            pivot.columns = display_judges

            fig, ax = plt.subplots(figsize=_COMPACT_JUDGE_SUMMARY_FIGSIZE)
            x = np.arange(len(pivot.index), dtype=float)
            group_width = 0.72
            bar_width = group_width / max(len(pivot.columns), 1)
            colors = _bar_palette(max(len(pivot.columns), 1))
            containers: list[BarContainer] = []
            offsets = (np.arange(len(pivot.columns), dtype=float) - (len(pivot.columns) - 1) / 2.0) * bar_width
            for idx, judge in enumerate(pivot.columns):
                bars = ax.bar(
                    x + offsets[idx],
                    pivot[judge].to_numpy(dtype=float),
                    width=bar_width * 0.92,
                    color=colors[idx],
                    label=judge,
                )
                containers.append(cast(BarContainer, bars))

                fig.suptitle("")
            ax.set_ylabel('排序得分', fontsize=12)
            ax.set_xlabel('方法', fontsize=12)
            ax.set_xticks(x)
            ax.set_xticklabels(list(pivot.index), rotation=0)
            ax.tick_params(axis='x', labelrotation=0)
            if fig._suptitle is not None:
                fig._suptitle.set_text("")
            ax.xaxis.label.set_size(_COMPACT_JUDGE_SUMMARY_LABEL_SIZE)
            ax.yaxis.label.set_size(_COMPACT_JUDGE_SUMMARY_LABEL_SIZE)
            ax.tick_params(axis='x', labelsize=_COMPACT_JUDGE_SUMMARY_TICK_SIZE)
            ax.tick_params(axis='y', labelsize=_COMPACT_JUDGE_SUMMARY_TICK_SIZE)
            fig.legend(
                handles=containers,
                labels=list(pivot.columns),
                loc='lower center',
                bbox_to_anchor=(0.5, 0.815),
                ncol=max(len(pivot.columns), 1),
                title=None,
                frameon=False,
            )
            legend = fig.legends[0] if fig.legends else None
            if legend is not None:
                legend.set_bbox_to_anchor((0.5, 0.81), transform=fig.transFigure)
                try:
                    legend.set_ncols(min(max(len(pivot.columns), 1), 3))
                except AttributeError:
                    pass
                for text in legend.get_texts():
                    text.set_fontsize(_COMPACT_JUDGE_SUMMARY_LEGEND_SIZE)
            for container in containers:
                ax.bar_label(container, fmt="{:.2f}", padding=2, fontsize=9)
            for text in ax.texts:
                text.set_fontsize(_COMPACT_JUDGE_SUMMARY_BAR_LABEL_SIZE)
            _apply_y_padding(ax, pivot.values.flatten())
            _style_axes(ax)
            _accentuate_bars(ax)
            plt.tight_layout(rect=(0, 0, 1, 0.88))
            plt.savefig(plots_dir / f'single_dim_by_judge_{dimension}.png', dpi=200)
            plt.close()


def plot_radar_overall(csv3: pd.DataFrame, out_dir: Path) -> None:
    """Plot overall radar charts (single circle) for generators and methods using judge-averaged scores."""
    plots_dir = out_dir / "plots" / "summary"
    plots_dir.mkdir(parents=True, exist_ok=True)

    dims = _ordered_dimensions(sorted(csv3["dimension"].dropna().unique().tolist()))
    if not dims:
        return

    angles = np.linspace(0, 2 * np.pi, len(dims), endpoint=False).tolist()
    angles += angles[:1]

    def _plot(entity_col: str, title: str, filename: str, label_positions: dict[str, tuple[float, float]], label_map: dict[str, str] | None = None, right_margin: float | None = None) -> None:
        data = weighted_avg_df(csv3, [entity_col, "dimension"])
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

        fig = plt.figure(figsize=_COMPACT_RADAR_FIGSIZE)
        ax = fig.add_subplot(111, polar=True)
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)
        theta_deg = np.degrees(angles[:-1])
        # Hide default tick labels and place custom labels at absolute positions
        ax.set_thetagrids(theta_deg, [""] * len(dims), fontsize=_COMPACT_RADAR_DIM_LABEL_SIZE)
        # Absolute positions in axes coordinates (0..1)
        for label, (x, y) in label_positions.items():
            ax.text(
                x,
                y,
                label,
                transform=ax.transAxes,
                ha="center",
                va="center",
                fontsize=_COMPACT_RADAR_DIM_LABEL_SIZE,
            )
        ax.set_ylim(0, 0.7)
        ax.set_yticks([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7])
        ax.set_yticklabels(
            ["0.1", "0.2", "0.3", "0.4", "0.5", "0.6", "0.7"],
            fontsize=_COMPACT_RADAR_RING_LABEL_SIZE,
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
            ax.plot(angles, values, color=color, linewidth=2.8, label=(label_map or {}).get(str(name), _display_label(str(name))))
            ax.fill(angles, values, color=color, alpha=0.15)

            ax.set_title("")
        if right_margin is not None:
            ax.legend(
                loc="upper right",
                bbox_to_anchor=(1.45, 1.08),
                frameon=False,
                fontsize=_COMPACT_RADAR_LEGEND_SIZE,
            )
        else:
            ax.legend(
                loc="upper right",
                bbox_to_anchor=(1.24, 1.08),
                frameon=False,
                fontsize=_COMPACT_RADAR_LEGEND_SIZE,
            )
            plt.tight_layout(pad=0.8)
        plt.savefig(plots_dir / filename, dpi=200, bbox_inches="tight")
        plt.close()

    generator_label_positions = {
        "有效性": (0.50, 1.02),
        "无干扰性": (1.00, 0.22),
        "可部署性": (0, 0.22),
    }
    method_label_positions = {
        "有效性": (0.50, 1.02),
        "无干扰性": (1.00, 0.22),
        "可部署性": (0, 0.22),
    }
    _plot("generator", "生成模型三维度雷达图", "radar_generator_overall.png", generator_label_positions)
    _plot("method", "方法配置三维度雷达图", "radar_method_overall.png", method_label_positions, right_margin=0.60)


def plot_radar_for_judge(csv3: pd.DataFrame, out_dir: Path, judge_key: str, label: str) -> None:
    """Plot radar charts using a single judge's scores (generator & method)."""
    plots_dir = out_dir / "plots" / "summary"
    plots_dir.mkdir(parents=True, exist_ok=True)

    judge_df = csv3[csv3["judge"] == judge_key]
    if judge_df.empty:
        return

    dims = _ordered_dimensions(sorted(judge_df["dimension"].dropna().unique().tolist()))
    if not dims:
        return

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

        fig = plt.figure(figsize=_COMPACT_RADAR_FIGSIZE)
        ax = fig.add_subplot(111, polar=True)
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)
        theta_deg = np.degrees(angles[:-1])
        ax.set_thetagrids(theta_deg, [""] * len(dims), fontsize=_COMPACT_RADAR_DIM_LABEL_SIZE)
        for lbl, (x, y) in label_positions.items():
            ax.text(
                x,
                y,
                lbl,
                transform=ax.transAxes,
                ha="center",
                va="center",
                fontsize=_COMPACT_RADAR_DIM_LABEL_SIZE,
            )
        ax.set_ylim(0, 1.0)
        ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
        ax.set_yticklabels(
            ["0.2", "0.4", "0.6", "0.8", "1.0"],
            fontsize=_COMPACT_RADAR_RING_LABEL_SIZE,
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
            ax.plot(angles, values, color=color, linewidth=2.8, label=_display_label(str(name)))
            ax.fill(angles, values, color=color, alpha=0.15)

            ax.set_title("")
        ax.legend(
            loc="upper right",
            bbox_to_anchor=(1.24, 1.08),
            frameon=False,
            fontsize=_COMPACT_RADAR_LEGEND_SIZE,
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


def plot_method_report(overall: pd.DataFrame, csv3: pd.DataFrame, out_dir: Path, dimension: str):
    report_dir = out_dir / "plots" / dimension / "method_report"
    report_dir.mkdir(parents=True, exist_ok=True)
    method_df = overall[(overall["dimension"] == dimension) & (overall["type"] == "method")].copy()
    if method_df.empty:
        return
    method_df = method_df.sort_values("avg_rank", ascending=False)
    method_df = _ensure_numeric(method_df, ["avg_rank"])
    labels = [_display_label(k) for k in method_df["key"].astype(str)]
    plt.figure(figsize=(6.0, 4.0))
    bars = plt.bar(labels, method_df["avg_rank"].astype(float), color=_bar_palette(len(labels)))
    plt.ylabel("排序得分", fontsize=12)
    plt.xlabel("方法", fontsize=12)
    plt.title(_title("方法总览：排序得分", dimension), fontsize=14, pad=12)
    plt.xticks(rotation=0, fontsize=10)
    ax = plt.gca()
    ax.bar_label(bars, fmt="{:.2f}", padding=2, fontsize=9)
    _apply_y_padding(ax, method_df["avg_rank"].to_numpy(dtype=float))
    _style_axes(ax)
    _accentuate_bars(ax)
    _add_y_axis_arrow(ax)
    plt.tight_layout()
    plt.savefig(report_dir / f"method_overview_{dimension}.png", dpi=200)
    plt.close()

    dim_cube = csv3[csv3["dimension"] == dimension]
    combos = weighted_avg_df(dim_cube, ["method", "generator"])
    if combos.empty:
        return
    method_order = method_df["key"].tolist()
    combos["method"] = pd.Categorical(combos["method"], categories=method_order, ordered=True)
    combos = combos.sort_values("method")
    pivot = combos.pivot(index="method", columns="generator", values="avg_rank")
    pivot.index = [_display_label(i) for i in pivot.index]
    pivot.columns = [_display_label(c) for c in pivot.columns]
    plt.figure(figsize=(6.4, 4.2))
    ax = sns.heatmap(pivot, annot=True, fmt=".2f", cmap=_HEATMAP_CMAP, cbar_kws={"shrink": 0.8})
    ax.set_title("")
    ax.set_xlabel("生成模型", fontsize=12)
    ax.set_ylabel("方法", fontsize=12)
    _style_axes(ax, grid_axis=None)
    plt.tight_layout()
    plt.savefig(report_dir / f"method_vs_generator_{dimension}.png", dpi=200)
    plt.close()


def plot_generator_report(overall: pd.DataFrame, csv3: pd.DataFrame, out_dir: Path, dimension: str):
    report_dir = out_dir / "plots" / dimension / "generator_report"
    report_dir.mkdir(parents=True, exist_ok=True)
    profile_df = overall[(overall["dimension"] == dimension) & (overall["type"] == "profile")].copy()
    if not profile_df.empty:
        profile_df = profile_df.sort_values("avg_rank", ascending=False)
        profile_df = _ensure_numeric(profile_df, ["avg_rank"])
        labels = [_display_label(k) for k in profile_df["key"].astype(str)]
        plt.figure(figsize=(6.0, 4.0))
        bars = plt.bar(labels, profile_df["avg_rank"].astype(float), color=_bar_palette(len(labels)))
        plt.ylabel("排序得分", fontsize=12)
        plt.xlabel("生成模型", fontsize=12)
        plt.title(_title("生成模型总览：排序得分", dimension), fontsize=14, pad=12)
        plt.xticks(rotation=0, fontsize=10)
        ax = plt.gca()
        ax.bar_label(bars, fmt="{:.2f}", padding=2, fontsize=9)
        _apply_y_padding(ax, profile_df["avg_rank"].to_numpy(dtype=float))
        _style_axes(ax)
        _accentuate_bars(ax)
        _add_y_axis_arrow(ax)
        plt.tight_layout()
        plt.savefig(report_dir / f"generator_overview_{dimension}.png", dpi=200)
        plt.close()

    dim_cube = csv3[csv3["dimension"] == dimension]
    combos = weighted_avg_df(dim_cube, ["generator", "method"])
    if combos.empty:
        return
    if not profile_df.empty:
        combos["generator"] = pd.Categorical(combos["generator"], categories=profile_df["key"].tolist(), ordered=True)
        combos = combos.sort_values("generator")
    pivot = combos.pivot(index="generator", columns="method", values="avg_rank")
    pivot.index = [_display_label(i) for i in pivot.index]
    pivot.columns = [_display_label(c) for c in pivot.columns]
    plt.figure(figsize=(6.4, 4.2))
    ax = sns.heatmap(pivot, annot=True, fmt=".2f", cmap=_HEATMAP_CMAP, cbar_kws={"shrink": 0.8})
    ax.set_title("")
    ax.set_xlabel("方法", fontsize=12)
    ax.set_ylabel("生成模型", fontsize=12)
    _style_axes(ax, grid_axis=None)
    plt.tight_layout()
    plt.savefig(report_dir / f"generator_vs_method_{dimension}.png", dpi=200)
    plt.close()


def plot_judge_report(csv3: pd.DataFrame, out_dir: Path, dimension: str):
    report_dir = out_dir / "plots" / dimension / "judge_report"
    report_dir.mkdir(parents=True, exist_ok=True)
    dim_cube = csv3[csv3["dimension"] == dimension]
    if dim_cube.empty:
        return

    judge_avg = weighted_avg_df(dim_cube, ["judge"])
    if not judge_avg.empty:
        judge_avg = _ensure_numeric(judge_avg, ["avg_rank"])
        judge_avg = judge_avg.sort_values("avg_rank", ascending=False)
        labels = [_display_label(j) for j in judge_avg["judge"].astype(str)]
        plt.figure(figsize=(6.0, 4.0))
        bars = plt.bar(labels, judge_avg["avg_rank"].astype(float), color=_bar_palette(len(labels), monochrome=True))
        plt.ylabel("排序得分", fontsize=12)
        plt.xlabel("评委模型", fontsize=12)
        plt.title(_title("评委模型总览：排序得分", dimension), fontsize=14, pad=12)
        plt.xticks(rotation=0, fontsize=10)
        ax = plt.gca()
        ax.bar_label(bars, fmt="{:.2f}", padding=2, fontsize=9)
        _apply_y_padding(ax, judge_avg["avg_rank"].to_numpy(dtype=float))
        _style_axes(ax)
        _accentuate_bars(ax)
        _add_y_axis_arrow(ax)
        plt.tight_layout()
        plt.savefig(report_dir / f"judge_overview_{dimension}.png", dpi=200)
        plt.close()

    judge_method = weighted_avg_df(dim_cube, ["judge", "method"])
    if not judge_method.empty:
        pivot = judge_method.pivot(index="judge", columns="method", values="avg_rank")
        pivot.index = [_display_label(i) for i in pivot.index]
        pivot.columns = [_display_label(c) for c in pivot.columns]
        plt.figure(figsize=(6.4, 4.2))
        ax = sns.heatmap(pivot, annot=True, fmt=".2f", cmap=_HEATMAP_CMAP, cbar_kws={"shrink": 0.8})
        ax.set_title("")
        ax.set_xlabel("方法", fontsize=12)
        ax.set_ylabel("评委模型", fontsize=12)
        _style_axes(ax, grid_axis=None)
        plt.tight_layout()
        plt.savefig(report_dir / f"judge_vs_method_{dimension}.png", dpi=200)
        plt.close()

    judge_generator = weighted_avg_df(dim_cube, ["judge", "generator"])
    if not judge_generator.empty:
        pivot = judge_generator.pivot(index="judge", columns="generator", values="avg_rank")
        pivot.index = [_display_label(i) for i in pivot.index]
        pivot.columns = [_display_label(c) for c in pivot.columns]
        plt.figure(figsize=(6.4, 4.2))
        ax = sns.heatmap(pivot, annot=True, fmt=".2f", cmap=_HEATMAP_CMAP, cbar_kws={"shrink": 0.8})
        ax.set_title("")
        ax.set_xlabel("生成模型", fontsize=12)
        ax.set_ylabel("评委模型", fontsize=12)
        _style_axes(ax, grid_axis=None)
        plt.tight_layout()
        plt.savefig(report_dir / f"judge_vs_generator_{dimension}.png", dpi=200)
        plt.close()


def plot_judge_consistency(csv3: pd.DataFrame, out_dir: Path) -> None:
    """Plot judge agreement/consistency using pairwise correlations and dispersion."""
    if csv3.empty:
        return

    plots_dir = out_dir / "plots" / "judge_consistency"
    plots_dir.mkdir(parents=True, exist_ok=True)

    df = csv3.copy()
    df = _ensure_numeric(df, ["avg_rank"])

    std_rows = []

    # Judge vectors over (generator, method) per dimension
    for dim in _ordered_dimensions(sorted(df["dimension"].dropna().unique().tolist())):
        sub = df[df["dimension"] == dim]
        pivot = sub.pivot_table(
            index=["generator", "method"],
            columns="judge",
            values="avg_rank",
            aggfunc="mean",
        )
        if pivot.empty:
            continue
        # Dispersion within this dimension
        std_series = pivot.std(axis=1)
        for val in std_series.values:
            if pd.notna(val):
                std_rows.append({"dimension": dim, "std_rank": float(val)})
        corr = pivot.corr(method="pearson", min_periods=1)
        plt.figure(figsize=_COMPACT_HEATMAP_FIGSIZE)
        cmap = _HEATMAP_CMAP
        try:
            cmap = _HEATMAP_CMAP.copy()
        except Exception:
            pass
        try:
            cmap.set_under("#FFFFFF")
        except Exception:
            pass
        ax = sns.heatmap(
            corr,
            annot=True,
            fmt=".2f",
            cmap=cmap,
            vmin=0.5,
            vmax=0.9,
            square=True,
            annot_kws={"size": _COMPACT_HEATMAP_ANNOT_SIZE, "weight": "medium"},
            cbar_kws={"shrink": 0.82, "extend": "min", "pad": 0.02},
        )
        ax.set_title("")
        ax.set_xlabel("评委模型", fontsize=12)
        ax.set_ylabel("评委模型", fontsize=12)
        _style_axes(ax, grid_axis=None)
        _style_colorbar(ax, "Pearson\n相关系数")
        plt.tight_layout()
        plt.savefig(plots_dir / f"judge_correlation_heatmap_{dim}.png", dpi=200)
        plt.close()

    # Dispersion by dimension (lower std => higher agreement)
    if std_rows:
        std_df = pd.DataFrame(std_rows)
        std_df = _ensure_numeric(std_df, ["std_rank"])
        dim_mean = std_df.groupby("dimension", as_index=False)["std_rank"].mean()
        if not dim_mean.empty:
            dim_order = _ordered_dimensions(dim_mean["dimension"].astype(str).tolist())
            dim_mean["dimension"] = pd.Categorical(dim_mean["dimension"], categories=dim_order, ordered=True)
            dim_mean = cast(Any, dim_mean).sort_values(by=["dimension"], ascending=True)
            plt.figure(figsize=(5.6, 4.0))
            bars = plt.bar(
                dim_mean["dimension"].astype(str).tolist(),
                dim_mean["std_rank"].astype(float).tolist(),
                color=_bar_palette(len(dim_mean), monochrome=True),
            )
            plt.ylabel("平均标准差", fontsize=15)
            plt.xlabel("维度", fontsize=15)
            ax = plt.gca()
            ax.bar_label(bars, fmt="{:.2f}", fontsize=12, padding=2)
            _style_axes(ax)
            plt.tight_layout()
            plt.savefig(plots_dir / "judge_dispersion_by_dimension.png", dpi=200)
            plt.close()


def _kendalls_w(rank_matrix: pd.DataFrame) -> Optional[float]:
    """Compute Kendall's W for a rank matrix (items x judges)."""
    if rank_matrix.empty:
        return None
    m = rank_matrix.shape[1]  # judges
    n = rank_matrix.shape[0]  # items
    if m < 2 or n < 2:
        return None
    # Sum ranks per item
    R = rank_matrix.sum(axis=1)
    R_bar = R.mean()
    S = ((R - R_bar) ** 2).sum()
    denom = m ** 2 * (n ** 3 - n)
    if denom == 0:
        return None
    return float(12 * S / denom)


def plot_judge_consistency_extended(csv3: pd.DataFrame, out_dir: Path) -> None:
    """Extended judge consistency plots: Kendall's W per dimension and pairwise Spearman."""
    if csv3.empty:
        return

    plots_dir = out_dir / "plots" / "judge_consistency"
    plots_dir.mkdir(parents=True, exist_ok=True)

    df = csv3.copy()
    df = _ensure_numeric(df, ["avg_rank"])

    w_rows = []
    spearman_rows = []

    for dim in _ordered_dimensions(sorted(df["dimension"].dropna().unique().tolist())):
        sub = df[df["dimension"] == dim]
        if sub.empty:
            continue
        pivot = sub.pivot_table(
            index=["generator", "method"],
            columns="judge",
            values="avg_rank",
            aggfunc="mean",
        )
        if pivot.empty:
            continue

        # Convert to ranks per judge (higher score is better, so best gets rank=1)
        rank_matrix = pivot.rank(axis=0, method="average", ascending=False)
        w = _kendalls_w(rank_matrix)
        if w is not None:
            w_rows.append({"dimension": dim, "kendalls_w": w})

        # Pairwise Spearman correlations across judges for this dimension
        corr = rank_matrix.corr(method="spearman", min_periods=1)
        judges = corr.columns.tolist()
        for i in range(len(judges)):
            for j in range(i + 1, len(judges)):
                val = corr.iloc[i, j]
                if pd.notna(val):
                    spearman_rows.append({"dimension": dim, "corr": float(val)})

    # Kendall's W bar chart
    if w_rows:
        w_df = pd.DataFrame(w_rows)
        dim_order = _ordered_dimensions(w_df["dimension"].astype(str).tolist())
        w_df["dimension"] = pd.Categorical(w_df["dimension"], categories=dim_order, ordered=True)
        w_df = w_df.sort_values("dimension")
        plt.figure(figsize=(5.6, 4.0))
        bars = plt.bar(
            w_df["dimension"].astype(str).tolist(),
            w_df["kendalls_w"].astype(float).tolist(),
            width=0.45,
            color=_bar_palette(len(w_df), monochrome=True),
        )
        plt.ylabel("Kendall's W", fontsize=12)
        plt.xlabel("维度", fontsize=12)
        plt.title("按维度：Kendall's W 一致性系数", fontsize=14, pad=12)
        ax = plt.gca()
        ax.bar_label(bars, fmt="{:.2f}", fontsize=9, padding=2)
        _style_axes(ax)
        _add_y_axis_arrow(ax)
        plt.tight_layout()
        plt.savefig(plots_dir / "judge_kendalls_w_by_dimension.png", dpi=200)
        plt.close()

    # Pairwise Spearman distribution by dimension
    if spearman_rows:
        s_df = pd.DataFrame(spearman_rows)
        dim_order = _ordered_dimensions(s_df["dimension"].astype(str).dropna().unique().tolist())
        plt.figure(figsize=(6.0, 4.2))
        ax = sns.boxplot(
            data=s_df,
            x="dimension",
            y="corr",
            order=dim_order,
            width=0.45,
            color="#A5A5A5",
            linewidth=1.0,
        )
        ax.set_title("")
        ax.set_xlabel("维度", fontsize=12)
        ax.set_ylabel("相关系数", fontsize=12)
        _style_axes(ax)
        plt.tight_layout()
        plt.savefig(plots_dir / "judge_spearman_box_by_dimension.png", dpi=200)
        plt.close()


def _format_top_rows(df: pd.DataFrame, key_col: str, value_col: str, top_k: int = 5) -> list[str]:
    if df.empty:
        return ["(无数据)"]
    rows = df.head(top_k)
    lines = []
    for _, row in rows.iterrows():
        key = _display_label(str(row.get(key_col, "")))
        val = row.get(value_col, None)
        if pd.isna(val):
            lines.append(f"- {key}: (缺失)")
        else:
            lines.append(f"- {key}: {float(val):.3f}")
    return lines


def write_text_report(overall: pd.DataFrame, by_judge: pd.DataFrame, csv3: pd.DataFrame, out_dir: Path) -> Path:
    """Generate a textual report summarizing numeric results for plots."""
    report_dir = out_dir / "plots"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "summary_report.txt"

    lines: list[str] = []
    lines.append("Kubernetes 安全评测图表数值报告")
    lines.append("=")
    lines.append("")

    dims = sorted(csv3["dimension"].dropna().unique())
    for dim in dims:
        lines.append(f"维度：{dim}")
        lines.append("-")

        method_df = overall[(overall["dimension"] == dim) & (overall["type"] == "method")].copy()
        method_df = _ensure_numeric(method_df, ["avg_rank"]).sort_values("avg_rank", ascending=False)
        lines.append("方法汇总（平均得分，Top 5）")
        lines.extend(_format_top_rows(method_df, "key", "avg_rank", top_k=5))
        lines.append("")

        profile_df = overall[(overall["dimension"] == dim) & (overall["type"] == "profile")].copy()
        profile_df = _ensure_numeric(profile_df, ["avg_rank"]).sort_values("avg_rank", ascending=False)
        lines.append("生成模型汇总（平均得分，Top 5）")
        lines.extend(_format_top_rows(profile_df, "key", "avg_rank", top_k=5))
        lines.append("")

        dim_cube = csv3[csv3["dimension"] == dim]
        judge_avg = weighted_avg_df(dim_cube, ["judge"])
        judge_avg = _ensure_numeric(judge_avg, ["avg_rank"]).sort_values("avg_rank", ascending=False)
        lines.append("评委模型汇总（加权平均得分，Top 5）")
        lines.extend(_format_top_rows(judge_avg, "judge", "avg_rank", top_k=5))
        lines.append("")

        # Best method per generator (Top 1)
        gen_method = weighted_avg_df(dim_cube, ["generator", "method"])
        gen_method = _ensure_numeric(gen_method, ["avg_rank"])
        if not gen_method.empty:
            lines.append("生成模型最佳方法（Top 1）")
            for gen in sorted(gen_method["generator"].dropna().unique()):
                sub = gen_method[gen_method["generator"] == gen].sort_values("avg_rank", ascending=False)
                if sub.empty:
                    continue
                top = sub.iloc[0]
                gen_label = _display_label(str(gen))
                method_label = _display_label(str(top.get("method", "")))
                val = top.get("avg_rank", None)
                if pd.isna(val):
                    lines.append(f"- {gen_label}: {method_label} (缺失)")
                else:
                    lines.append(f"- {gen_label}: {method_label} ({float(val):.3f})")
            lines.append("")

        # Best generator per method (Top 1)
        method_gen = weighted_avg_df(dim_cube, ["method", "generator"])
        method_gen = _ensure_numeric(method_gen, ["avg_rank"])
        if not method_gen.empty:
            lines.append("方法最佳生成模型（Top 1）")
            for method in sorted(method_gen["method"].dropna().unique()):
                sub = method_gen[method_gen["method"] == method].sort_values("avg_rank", ascending=False)
                if sub.empty:
                    continue
                top = sub.iloc[0]
                method_label = _display_label(str(method))
                gen_label = _display_label(str(top.get("generator", "")))
                val = top.get("avg_rank", None)
                if pd.isna(val):
                    lines.append(f"- {method_label}: {gen_label} (缺失)")
                else:
                    lines.append(f"- {method_label}: {gen_label} ({float(val):.3f})")
            lines.append("")

        # Per-judge top method (Top 1)
        judge_method = weighted_avg_df(dim_cube, ["judge", "method"])
        judge_method = _ensure_numeric(judge_method, ["avg_rank"])
        if not judge_method.empty:
            lines.append("评委模型最佳方法（Top 1）")
            for judge in sorted(judge_method["judge"].dropna().unique()):
                sub = judge_method[judge_method["judge"] == judge].sort_values("avg_rank", ascending=False)
                if sub.empty:
                    continue
                top = sub.iloc[0]
                judge_label = _display_label(str(judge))
                method_label = _display_label(str(top.get("method", "")))
                val = top.get("avg_rank", None)
                if pd.isna(val):
                    lines.append(f"- {judge_label}: {method_label} (缺失)")
                else:
                    lines.append(f"- {judge_label}: {method_label} ({float(val):.3f})")
            lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--in-dir", type=Path, default=Path("images") / "analysis", help="输入 CSV 文件目录")
    p.add_argument("--out-dir", type=Path, default=Path("images"), help="图表输出根目录（图表写入 {out-dir}/plots/）")
    p.add_argument("--dimensions", nargs="*", default=None, help="维度名称列表，默认全部")
    p.add_argument("--single-dim", nargs="*", default=None, help="只生成单维度总结图 (传入维度名列表)")
    args = p.parse_args()

    in_dir: Path = args.in_dir
    out_dir: Path = args.out_dir

    overall, by_judge, csv3 = load_csvs(in_dir)
    dims = args.dimensions or sorted(csv3["dimension"].unique())
    if args.single_dim:
        for d in args.single_dim:
            plot_single_dimension(out_dir, d, in_dir=in_dir)
            plot_method_report(overall, csv3, out_dir, d)
            plot_generator_report(overall, csv3, out_dir, d)
    else:
        for d in dims:
            plot_grouped_bar(csv3, out_dir, d)
            plot_heatmap(csv3, out_dir, d)
            plot_per_method(csv3, out_dir, d)
            plot_per_generator(csv3, out_dir, d)
            plot_single_dimension(out_dir, d, in_dir=in_dir)
            plot_method_report(overall, csv3, out_dir, d)
            plot_generator_report(overall, csv3, out_dir, d)
    plot_radar_overall(csv3, out_dir)
    plot_radar_for_judge(csv3, out_dir, "gpt5", "GPT-5")
    plot_judge_consistency(csv3, out_dir)
    plot_judge_consistency_extended(csv3, out_dir)
    report_path = write_text_report(overall, by_judge, csv3, out_dir)
    print(f"Plots written to {out_dir / 'plots'}")
    print(f"Text report written to {report_path}")
