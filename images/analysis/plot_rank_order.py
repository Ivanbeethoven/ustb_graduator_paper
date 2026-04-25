#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

DIMENSIONS = ["有效性", "无干扰性", "可部署性"]

# Paper-friendly LLM legend labels (do not use raw profile keys)
LLM_LEGEND = [
    ("qwen", "Qwen3-Max", "qwen.png"),
    ("deepseek", "DeepSeekV3.2", "deepseek.png"),
    ("glm", "GLM-4.5", "glm.png"),
    ("gpt", "GPT-5", "gpt.png"),
    ("grok", "Grok 4", "grok.png"),
]

LLM_BADGES = {
    "qwen": {"abbr": "Q", "color": "#E85D75"},
    "deepseek": {"abbr": "DS", "color": "#6C8F2A"},
    "glm": {"abbr": "GLM", "color": "#2FAE78"},
    "gpt": {"abbr": "GPT", "color": "#2EA6C7"},
    "grok": {"abbr": "G", "color": "#B06AF3"},
}

plt.rcParams.update(
    {
        "figure.dpi": 150,
        "savefig.dpi": 200,
        "axes.unicode_minus": False,
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
        "font.size": 14,
        "axes.facecolor": "#FFFFFF",
        "figure.facecolor": "#FFFFFF",
        "axes.edgecolor": "#2A2A2A",
        "axes.labelcolor": "#1F1F1F",
        "xtick.color": "#1F1F1F",
        "ytick.color": "#1F1F1F",
        "grid.color": "#CFCFCF",
        "grid.linestyle": "--",
        "grid.linewidth": 0.6,
        "legend.frameon": False,
    }
)

COMPACT_RANK_FIGSIZE = (8.6, 4.7)
COMPACT_ICON_FIGSIZE = (9.0, 4.9)
COMPACT_TITLE_SIZE = 19
COMPACT_AXIS_LABEL_SIZE = 16
COMPACT_TICK_SIZE = 15
COMPACT_LEGEND_TITLE_SIZE = 14
COMPACT_LEGEND_TEXT_SIZE = 13
COMPACT_MARKER_SIZE = 210
COMPACT_MARKER_LEGEND_SIZE = 6.5
COMPACT_ICON_ZOOM = 0.17
COMPACT_ICON_LEGEND_ZOOM = 0.08


def _safe_label(name: str) -> str:
    if name is None:
        return ""
    s = str(name)
    if s == "all":
        return "KPEDefense"
    if s.startswith("no_"):
        suffix = s[3:].replace("_", " ")
        display_suffix = suffix.upper() if len(suffix) <= 4 else suffix.capitalize()
        return "KPEDefense w/o " + display_suffix
    return s.replace("_", " ")


def _to_markdown_safe(df: pd.DataFrame) -> str:
    try:
        return df.to_markdown(index=False)
    except ImportError:
        return df.to_string(index=False)


def _generate_report(method_ranks: pd.DataFrame, profile_ranks: pd.DataFrame, dims: List[str], out_dir: Path) -> None:
    """生成论文用的统计报告（Markdown + LaTeX表格）"""
    report_lines = []
    report_lines.append("# 策略生成综合评估报告\n")
    report_lines.append(f"生成时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report_lines.append("---\n")
    
    # 方法排名部分
    report_lines.append("## 1. 方法对比排名\n")
    if not method_ranks.empty:
        method_ranks_display = method_ranks.copy()
        method_ranks_display['方法'] = method_ranks_display['key'].map(_safe_label)
        cols = ['方法'] + dims
        method_table = method_ranks_display[cols]
        report_lines.append("### 排名表格（数值越小越好）\n")
        report_lines.append(_to_markdown_safe(method_table))
        report_lines.append("\n")
        
        # 计算平均排名
        method_ranks_display['平均排名'] = method_ranks_display[dims].mean(axis=1)
        method_ranks_display = method_ranks_display.sort_values('平均排名')
        report_lines.append("### 综合平均排名\n")
        avg_table = method_ranks_display[['方法', '平均排名']]
        report_lines.append(_to_markdown_safe(avg_table))
        report_lines.append("\n")
        
        # LaTeX表格
        report_lines.append("### LaTeX表格代码\n")
        report_lines.append("```latex\n")
        report_lines.append("\\begin{table}[htbp]\n")
        report_lines.append("\\centering\n")
        report_lines.append("\\caption{方法对比排名结果}\n")
        report_lines.append("\\begin{tabular}{l" + "c" * len(dims) + "c}\n")
        report_lines.append("\\hline\n")
        report_lines.append("方法 & " + " & ".join(dims) + " & 平均排名 \\\\\n")
        report_lines.append("\\hline\n")
        for _, row in method_ranks_display.iterrows():
            values = [f"{row[d]:.1f}" for d in dims]
            report_lines.append(f"{row['方法']} & " + " & ".join(values) + f" & {row['平均排名']:.2f} \\\\\n")
        report_lines.append("\\hline\n")
        report_lines.append("\\end{tabular}\n")
        report_lines.append("\\end{table}\n")
        report_lines.append("```\n\n")
    
    # 模型排名部分
    report_lines.append("## 2. 生成模型对比排名\n")
    if not profile_ranks.empty:
        profile_ranks_display = profile_ranks.copy()
        profile_ranks_display['模型'] = profile_ranks_display['key'].map(_safe_label)
        cols = ['模型'] + dims
        profile_table = profile_ranks_display[cols]
        report_lines.append("### 排名表格（数值越小越好）\n")
        report_lines.append(_to_markdown_safe(profile_table))
        report_lines.append("\n")
        
        # 计算平均排名
        profile_ranks_display['平均排名'] = profile_ranks_display[dims].mean(axis=1)
        profile_ranks_display = profile_ranks_display.sort_values('平均排名')
        report_lines.append("### 综合平均排名\n")
        avg_table = profile_ranks_display[['模型', '平均排名']]
        report_lines.append(_to_markdown_safe(avg_table))
        report_lines.append("\n")
        
        # LaTeX表格
        report_lines.append("### LaTeX表格代码\n")
        report_lines.append("```latex\n")
        report_lines.append("\\begin{table}[htbp]\n")
        report_lines.append("\\centering\n")
        report_lines.append("\\caption{生成模型对比排名结果}\n")
        report_lines.append("\\begin{tabular}{l" + "c" * len(dims) + "c}\n")
        report_lines.append("\\hline\n")
        report_lines.append("模型 & " + " & ".join(dims) + " & 平均排名 \\\\\n")
        report_lines.append("\\hline\n")
        for _, row in profile_ranks_display.iterrows():
            values = [f"{row[d]:.1f}" for d in dims]
            report_lines.append(f"{row['模型']} & " + " & ".join(values) + f" & {row['平均排名']:.2f} \\\\\n")
        report_lines.append("\\hline\n")
        report_lines.append("\\end{tabular}\n")
        report_lines.append("\\end{table}\n")
        report_lines.append("```\n\n")
    
    # 关键发现
    report_lines.append("## 3. 关键发现\n")
    if not method_ranks.empty:
        method_ranks_display = method_ranks.copy()
        method_ranks_display['方法'] = method_ranks_display['key'].map(_safe_label)
        method_ranks_display['平均排名'] = method_ranks_display[dims].mean(axis=1)
        best_method = method_ranks_display.loc[method_ranks_display['平均排名'].idxmin()]
        report_lines.append(f"- **最佳方法**: {best_method['方法']} (平均排名: {best_method['平均排名']:.2f})\n")
        
        for dim in dims:
            best_in_dim = method_ranks_display.loc[method_ranks_display[dim].idxmin()]
            report_lines.append(f"- **{dim}最佳**: {best_in_dim['方法']} (排名: {best_in_dim[dim]:.1f})\n")
    
    if not profile_ranks.empty:
        profile_ranks_display = profile_ranks.copy()
        profile_ranks_display['模型'] = profile_ranks_display['key'].map(_safe_label)
        profile_ranks_display['平均排名'] = profile_ranks_display[dims].mean(axis=1)
        best_profile = profile_ranks_display.loc[profile_ranks_display['平均排名'].idxmin()]
        report_lines.append(f"\n- **最佳生成模型**: {best_profile['模型']} (平均排名: {best_profile['平均排名']:.2f})\n")
        
        for dim in dims:
            best_in_dim = profile_ranks_display.loc[profile_ranks_display[dim].idxmin()]
            report_lines.append(f"- **{dim}最佳模型**: {best_in_dim['模型']} (排名: {best_in_dim[dim]:.1f})\n")
    
    report_lines.append("\n---\n")
    report_lines.append("*本报告由plot_rank_order.py自动生成*\n")
    
    # 写入报告文件
    report_path = out_dir / "ranking_report.md"
    report_path.write_text("".join(report_lines), encoding="utf-8")
    print(f"[报告] 已生成论文报告: {report_path}")


def _bw_palette(n: int) -> List:
    if n <= 1:
        return ["#202020"]
    shades = np.linspace(0.15, 0.85, n)
    return [plt.cm.Greys(s) for s in shades]


def _add_x_axis_arrow(ax: plt.Axes) -> None:
    ax.annotate(
        "",
        xy=(1.02, 0),
        xytext=(0, 0),
        xycoords="axes fraction",
        arrowprops=dict(arrowstyle="->", color="#1F1F1F", lw=1.0),
        annotation_clip=False,
    )


def _method_markers(n: int) -> List[str]:
    base = ["o", "s", "^", "D", "P", "X", "v", "<", ">"]
    if n <= len(base):
        return base[:n]
    repeats = (n // len(base)) + 1
    return (base * repeats)[:n]


def _y_map(dims: List[str], step: float = 0.68, base: float = 0.72) -> dict:
    return {d: base + i * step for i, d in enumerate(dims)}


def _llm_icon_path(name: str, llm_dir: Path) -> Path | None:
    if not name:
        return None
    s = str(name).lower()
    # Use ordered legend mapping for icon resolution
    for token, _label, fname in LLM_LEGEND:
        if token in s:
            cand = llm_dir / fname
            if cand.exists():
                return cand
    fallback_names = []
    if "gpt" in s:
        fallback_names.extend(["gpt.png", "gpt5.png"])
    if "grok" in s or "gork" in s:
        fallback_names.extend(["grok.png", "gork.png"])
    for fname in fallback_names:
        cand = llm_dir / fname
        if cand.exists():
            return cand
    return None


def _load_square_icon(path: Path) -> np.ndarray:
    img = plt.imread(path)
    if img.ndim == 2:
        img = np.stack([img, img, img], axis=-1)
    if img.shape[-1] == 3:
        alpha = np.ones((img.shape[0], img.shape[1], 1), dtype=img.dtype)
        img = np.concatenate([img, alpha], axis=-1)
    alpha_mask = img[..., 3] > 0.02
    if np.any(alpha_mask):
        ys, xs = np.where(alpha_mask)
        y0, y1 = ys.min(), ys.max() + 1
        x0, x1 = xs.min(), xs.max() + 1
        img = img[y0:y1, x0:x1]
    h, w = img.shape[:2]
    side = max(h, w)
    canvas = np.zeros((side, side, 4), dtype=img.dtype)
    y0 = (side - h) // 2
    x0 = (side - w) // 2
    canvas[y0:y0 + h, x0:x0 + w] = img
    return canvas


def _llm_badge_spec(name: str) -> dict[str, str]:
    s = str(name).lower()
    for token, spec in LLM_BADGES.items():
        if token in s or (token == "grok" and "gork" in s):
            return spec
    return {"abbr": str(name)[:2].upper(), "color": "#303030"}


def _draw_badge(ax: plt.Axes, x: float, y: float, name: str, size: int = 230, *, transform=None) -> None:
    spec = _llm_badge_spec(name)
    text_size = 8 if len(spec["abbr"]) >= 3 else 10
    ax.scatter(
        [x],
        [y],
        s=size,
        color=spec["color"],
        edgecolors="#FFFFFF",
        linewidths=1.6,
        transform=transform,
        zorder=4,
    )
    ax.text(
        x,
        y,
        spec["abbr"],
        color="#FFFFFF",
        ha="center",
        va="center",
        fontsize=text_size,
        fontweight="bold",
        transform=transform,
        zorder=5,
    )


def _add_llm_legend(fig: plt.Figure, ranks: pd.DataFrame, llm_dir: Path) -> None:
    """Add an icon+text legend on the right side showing each model's full name."""
    if ranks.empty:
        return
    # Always show the fixed set of models in the legend (paper-friendly)
    legend_items = list(LLM_LEGEND)

    # Create a dedicated legend area (right side)
    # Noticeably further right to improve overall balance
    ax_leg = fig.add_axes([0.80, 0.16, 0.18, 0.68])
    ax_leg.set_axis_off()

    n = len(legend_items)
    ys = np.linspace(0.82, 0.12, n)
    for i, (_token, label, fname) in enumerate(legend_items):
        y = float(ys[i])
        icon_path = _llm_icon_path(label, llm_dir)
        if icon_path and icon_path.exists():
            img = _load_square_icon(icon_path)
            imagebox = OffsetImage(img, zoom=COMPACT_ICON_LEGEND_ZOOM)
            ab = AnnotationBbox(
                imagebox,
                (0.20, y),
                xycoords=ax_leg.transAxes,
                frameon=False,
            )
            ax_leg.add_artist(ab)
        else:
            _draw_badge(ax_leg, 0.20, y, label, size=250, transform=ax_leg.transAxes)

        ax_leg.text(
            0.32,
            y,
            label,
            va="center",
            ha="left",
            fontsize=COMPACT_LEGEND_TEXT_SIZE,
            color="#1F1F1F",
            transform=ax_leg.transAxes,
        )


def _rank_order(df: pd.DataFrame, dims: List[str]) -> pd.DataFrame:
    pivot = df.pivot_table(index="key", columns="dimension", values="avg_rank", aggfunc="mean")
    pivot = pivot.reindex(columns=dims)
    ranks = pivot.rank(axis=0, method="average", ascending=True)
    ranks = ranks.reset_index().rename_axis(None, axis=1)
    return ranks


def _plot_rank_markers(
    ranks: pd.DataFrame, dims: List[str], title: str, out_path: Path
) -> None:
    if ranks.empty:
        return
    ranks = ranks.copy()
    ranks["label"] = ranks["key"].astype(str).map(_safe_label)

    fig, ax = plt.subplots(figsize=COMPACT_RANK_FIGSIZE)
    colors = ["#202020"] * len(ranks)
    markers = _method_markers(len(ranks))

    y_map = _y_map(dims)
    for i, row in ranks.iterrows():
        for d in dims:
            x = row[d]
            y = y_map[d]
            ax.scatter(x, y, color=colors[i], s=COMPACT_MARKER_SIZE, marker=markers[i], zorder=3)

            ax.set_title("")
    ax.set_xlabel("排序（名次）", fontsize=14)
    ax.set_ylabel("维度", fontsize=14)
    ax.set_yticks(list(y_map.values()))
    ax.set_yticklabels(dims, fontsize=13)
    ax.set_xticks(range(1, len(ranks) + 1))
    ax.tick_params(axis="x", labelsize=13)
    ax.tick_params(axis="y", labelsize=13)
    ax.title.set_fontsize(COMPACT_TITLE_SIZE)
    ax.title.set_y(1.01)
    ax.xaxis.label.set_size(COMPACT_AXIS_LABEL_SIZE)
    ax.yaxis.label.set_size(COMPACT_AXIS_LABEL_SIZE)
    ax.tick_params(axis="x", labelsize=COMPACT_TICK_SIZE)
    ax.tick_params(axis="y", labelsize=COMPACT_TICK_SIZE)
    ax.set_xlim(0.5, len(ranks) + 0.5)
    y_min = min(y_map.values()) - 0.35
    y_max = max(y_map.values()) + 0.35
    ax.set_ylim(y_min, y_max)
    ax.set_axisbelow(True)
    ax.grid(axis="x", visible=False)
    ax.grid(axis="y", alpha=0.75)
    for spine_name, spine in ax.spines.items():
        if spine_name in {"top", "right"}:
            spine.set_visible(False)
        else:
            spine.set_color("#2A2A2A")
            spine.set_linewidth(0.8)

    handles = [
        plt.Line2D(
            [0],
            [0],
            marker=markers[i],
            color=colors[i],
            linestyle="",
            markersize=COMPACT_MARKER_LEGEND_SIZE,
        )
        for i in range(len(ranks))
    ]
    leg = ax.legend(
        handles,
        ranks["label"].tolist(),
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        fontsize=COMPACT_LEGEND_TEXT_SIZE,
        title="方法",
    )
    if leg is not None:
        leg.get_title().set_fontsize(COMPACT_LEGEND_TITLE_SIZE)
        leg.set_frame_on(True)
        frame = leg.get_frame()
        frame.set_edgecolor("#1F1F1F")
        frame.set_linewidth(0.9)
        frame.set_facecolor("#FFFFFF")
    _add_x_axis_arrow(ax)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


def _plot_rank_icons(
    ranks: pd.DataFrame, dims: List[str], title: str, out_path: Path, llm_dir: Path
) -> None:
    if ranks.empty:
        return
    ranks = ranks.copy()
    ranks["label"] = ranks["key"].astype(str).map(_safe_label)

    fig, ax = plt.subplots(figsize=COMPACT_ICON_FIGSIZE)
    y_map = _y_map(dims)

    for _, row in ranks.iterrows():
        icon_path = _llm_icon_path(row["key"], llm_dir)
        for d in dims:
            x = row[d]
            y = y_map[d]
            if icon_path and icon_path.exists():
                img = _load_square_icon(icon_path)
                imagebox = OffsetImage(img, zoom=COMPACT_ICON_ZOOM)
                ab = AnnotationBbox(imagebox, (x, y), frameon=False)
                ax.add_artist(ab)
            else:
                _draw_badge(ax, x, y, row["key"], size=260)

                ax.set_title("")
    ax.set_xlabel("排序（名次）", fontsize=14)
    ax.set_ylabel("维度", fontsize=14)
    ax.set_yticks(list(y_map.values()))
    ax.set_yticklabels(dims, fontsize=13)
    ax.set_xticks(range(1, len(ranks) + 1))
    ax.tick_params(axis="x", labelsize=13)
    ax.tick_params(axis="y", labelsize=13)
    ax.title.set_fontsize(COMPACT_TITLE_SIZE)
    ax.title.set_y(1.01)
    ax.xaxis.label.set_size(COMPACT_AXIS_LABEL_SIZE)
    ax.yaxis.label.set_size(COMPACT_AXIS_LABEL_SIZE)
    ax.tick_params(axis="x", labelsize=COMPACT_TICK_SIZE)
    ax.tick_params(axis="y", labelsize=COMPACT_TICK_SIZE)
    ax.set_xlim(0.5, len(ranks) + 0.5)
    y_min = min(y_map.values()) - 0.35
    y_max = max(y_map.values()) + 0.35
    ax.set_ylim(y_min, y_max)
    ax.set_axisbelow(True)
    ax.grid(axis="x", visible=False)
    ax.grid(axis="y", alpha=0.75)
    _add_x_axis_arrow(ax)
    for spine_name, spine in ax.spines.items():
        if spine_name in {"top", "right"}:
            spine.set_visible(False)
        else:
            spine.set_color("#2A2A2A")
            spine.set_linewidth(0.8)

    _add_llm_legend(fig, ranks, llm_dir)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Leave room on the right for the legend area
    # Leave more gap between plot and legend
    fig.subplots_adjust(left=0.10, right=0.73, top=0.90, bottom=0.14)
    plt.savefig(out_path, dpi=200)
    plt.close()


def main() -> None:
    p = argparse.ArgumentParser(description="Plot rank order (slope graph) from analysis_summary.csv")
    p.add_argument(
        "--summary-csv",
        type=Path,
        default=Path.cwd() / "analysis" / "analysis_summary.csv",
        help="analysis_summary.csv 路径",
    )
    p.add_argument(
        "--out-dir",
        type=Path,
        default=Path.cwd() / "analysis" / "output_rank_order",
        help="输出目录",
    )
    p.add_argument(
        "--llm-dir",
        type=Path,
        default=Path.cwd() / "images" / "llms",
        help="LLM 图标目录",
    )
    args = p.parse_args()

    print("="*70)
    print("策略生成综合评估 - 排名分析")
    print("="*70)
    print(f"\n[数据] 读取分析数据: {args.summary_csv}")
    df = pd.read_csv(args.summary_csv)
    print(f"[数据] 总记录数: {len(df)}")
    print(f"[数据] 评估维度: {df['dimension'].unique().tolist()}")
    
    dims = [d for d in DIMENSIONS if d in df["dimension"].unique().tolist()]
    if not dims:
        dims = DIMENSIONS
    print(f"[数据] 使用维度: {dims}")

    method_df = df[(df["type"] == "method") & (df["dimension"].isin(dims))].copy()
    profile_df = df[(df["type"] == "profile") & (df["dimension"].isin(dims))].copy()
    
    print(f"\n[统计] 方法数量: {method_df['key'].nunique()}")
    print(f"[统计] 模型数量: {profile_df['key'].nunique()}")

    method_ranks = _rank_order(method_df, dims)
    profile_ranks = _rank_order(profile_df, dims)
    
    # 打印方法排名
    if not method_ranks.empty:
        print("\n" + "="*70)
        print("方法排名结果")
        print("="*70)
        method_display = method_ranks.copy()
        method_display['方法'] = method_display['key'].map(_safe_label)
        method_display['平均排名'] = method_display[dims].mean(axis=1)
        method_display = method_display.sort_values('平均排名')
        print(method_display[['方法'] + dims + ['平均排名']].to_string(index=False))
        best = method_display.iloc[0]
        print(f"\n[结果] 最佳方法: {best['方法']} (平均排名: {best['平均排名']:.2f})")
    
    # 打印模型排名
    if not profile_ranks.empty:
        print("\n" + "="*70)
        print("生成模型排名结果")
        print("="*70)
        profile_display = profile_ranks.copy()
        profile_display['模型'] = profile_display['key'].map(_safe_label)
        profile_display['平均排名'] = profile_display[dims].mean(axis=1)
        profile_display = profile_display.sort_values('平均排名')
        print(profile_display[['模型'] + dims + ['平均排名']].to_string(index=False))
        best = profile_display.iloc[0]
        print(f"\n[结果] 最佳模型: {best['模型']} (平均排名: {best['平均排名']:.2f})")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*70)
    print("生成可视化图表")
    print("="*70)
    _plot_rank_markers(
        method_ranks,
        dims,
        "方法综合排序结果",
        args.out_dir / "method_rank_order.png",
    )
    print(f"[图表] 方法排名图: {args.out_dir / 'method_rank_order.png'}")
    
    _plot_rank_icons(
        profile_ranks,
        dims,
        "生成模型综合排序结果",
        args.out_dir / "profile_rank_order.png",
        args.llm_dir,
    )
    print(f"[图表] 模型排名图: {args.out_dir / 'profile_rank_order.png'}")
    
    # 生成论文报告
    print("\n" + "="*70)
    print("生成论文报告")
    print("="*70)
    _generate_report(method_ranks, profile_ranks, dims, args.out_dir)
    
    print("\n" + "="*70)
    print(f"[完成] 所有结果已输出至: {args.out_dir}")
    print("="*70)


if __name__ == "__main__":
    main()
