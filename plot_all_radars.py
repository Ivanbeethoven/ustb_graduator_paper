#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pandas", "matplotlib", "seaborn", "numpy"]
# ///
"""
统一绘制两张组合雷达图：
  (a) 生成模型对比：人工评审 | 多源模型评审（共享图例）
  (b) 方法配置对比：人工评审 | 多源模型评审（共享图例）
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid", rc={"axes.unicode_minus": False})
plt.rcParams.update({
    "font.sans-serif": [
        "WenQuanYi Micro Hei", "WenQuanYi Zen Hei",
        "Noto Sans CJK SC", "Microsoft YaHei", "SimHei", "DejaVu Sans",
    ],
    "font.family": "sans-serif",
    "font.size": 10,
    "figure.dpi": 150, "savefig.dpi": 200,
})

OUT_DIR = Path(__file__).parent / "images"

# ============================================================
# 硬编码数据
# 维度顺序：有效性、无干扰性、可部署性
# ============================================================
DIMS = ["有效性", "无干扰性", "可部署性"]

# --- (a) 人工评审 - 生成模型 ---
HUMAN_GENERATOR = {
    "Qwen3-Max":     [0.250957, 0.366071, 0.293233],
    "DeepSeekV3.2":  [0.614923, 0.613252, 0.607143],
    "GLM-4.5":       [0.536432, 0.465461, 0.520912],
    "GPT-5":         [0.645337, 0.595630, 0.654135],
    "Grok 4":        [0.450945, 0.459586, 0.424577],
}

# --- (b) 多源模型评审 - 生成模型 ---
LLM_GENERATOR = {
    "Qwen3-Max":     [0.346037, 0.534086, 0.576198],
    "DeepSeekV3.2":  [0.419500, 0.592381, 0.679724],
    "GLM-4.5":       [0.454759, 0.452186, 0.461588],
    "GPT-5":         [0.848931, 0.331681, 0.189577],
    "Grok 4":        [0.308402, 0.466735, 0.469852],
}

# --- (c) 人工评审 - 方法配置 ---
HUMAN_METHOD = {
    "KPEDefense":              [0.674279, 0.599060, 0.656015],
    "KPEDefense w/o COT":      [0.476138, 0.425752, 0.420301],
    "KPEDefense w/o Feedback": [0.397368, 0.375376, 0.381203],
    "KPEDefense w/o RAG":      [0.452611, 0.599812, 0.542481],
}

# --- (d) 多源模型评审 - 方法配置 ---
LLM_METHOD = {
    "KPEDefense":              [0.660557, 0.539050, 0.516508],
    "KPEDefense w/o COT":      [0.379133, 0.465507, 0.512104],
    "KPEDefense w/o Feedback": [0.287396, 0.407509, 0.423107],
    "KPEDefense w/o RAG":      [0.575102, 0.489736, 0.450068],
}

# ============================================================
# 绘图参数
# ============================================================
SUBPLOT_FIGSIZE = (12.5, 5.8)
DIM_LABEL_SIZE = 20
RING_LABEL_SIZE = 10
LEGEND_SIZE = 15
LINE_WIDTH = 2.8
FILL_ALPHA = 0.15

LABEL_POSITIONS = {
    "有效性":   (0.50, 1.02),
    "无干扰性": (1.00, 0.22),
    "可部署性": (0.00, 0.22),
}


def draw_radar_on_axis(
    ax,
    data: dict[str, list[float]],
    color_map: dict[str, tuple[float, float, float]],
    ylim_max: float = 0.7,
    yticks: list[float] | None = None,
) -> list:
    angles = np.linspace(0, 2 * np.pi, len(DIMS), endpoint=False).tolist()
    angles += angles[:1]

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    theta_deg = np.degrees(angles[:-1])
    ax.set_thetagrids(theta_deg, [""] * len(DIMS), fontsize=DIM_LABEL_SIZE)

    for label, (x, y) in LABEL_POSITIONS.items():
        ax.text(x, y, label, transform=ax.transAxes, ha="center", va="center",
                fontsize=DIM_LABEL_SIZE)

    ax.set_ylim(0, ylim_max)
    if yticks is None:
        step = 0.1 if ylim_max <= 0.7 else 0.2
        yticks = [round(step * i, 1) for i in range(1, int(ylim_max / step) + 1)]
    ax.set_yticks(yticks)
    ax.set_yticklabels([str(t) for t in yticks], fontsize=RING_LABEL_SIZE)
    ax.grid(color="#D0D0D0", linestyle="--", linewidth=0.6, alpha=0.9)

    handles = []
    for name, values in data.items():
        vals = list(values) + [values[0]]
        color = color_map[name]
        line, = ax.plot(angles, vals, color=color, linewidth=LINE_WIDTH, label=name)
        ax.fill(angles, vals, color=color, alpha=FILL_ALPHA)
        handles.append(line)

    ax.set_title("")
    return handles


def draw_combined_radar_pair(
    left_data: dict[str, list[float]],
    right_data: dict[str, list[float]],
    filename: str,
    left_title: str,
    right_title: str,
    ylim_max: float = 0.7,
    legend_ncol: int = 1,
    legend_y: float = 0.03,
) -> None:
    labels = list(left_data.keys())
    palette = sns.color_palette("husl", n_colors=len(labels))
    color_map = {name: color for name, color in zip(labels, palette)}

    fig, (ax_left, ax_right) = plt.subplots(
        1, 2, figsize=SUBPLOT_FIGSIZE, subplot_kw={"polar": True}
    )

    handles = draw_radar_on_axis(ax_left, left_data, color_map, ylim_max=ylim_max)
    draw_radar_on_axis(ax_right, right_data, color_map, ylim_max=ylim_max)

    ax_left.text(
        0.02, 0.98, left_title,
        transform=ax_left.transAxes,
        ha="left", va="top", fontsize=16,
    )
    ax_right.text(
        0.02, 0.98, right_title,
        transform=ax_right.transAxes,
        ha="left", va="top", fontsize=16,
    )

    fig.legend(
        handles,
        labels,
        loc="lower center",
        bbox_to_anchor=(0.5, legend_y),
        frameon=False,
        fontsize=LEGEND_SIZE,
        ncol=legend_ncol,
    )

    plt.tight_layout(rect=(0, 0.10, 1, 1), pad=1.0)
    out_path = OUT_DIR / filename
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"✓ {out_path}")


if __name__ == "__main__":
    draw_combined_radar_pair(
        HUMAN_GENERATOR,
        LLM_GENERATOR,
        "combined/generator_radar_combined.png",
        left_title="人工评审",
        right_title="多源模型评审",
        ylim_max=0.7,
        legend_ncol=3,
        legend_y=0.01,
    )

    draw_combined_radar_pair(
        HUMAN_METHOD,
        LLM_METHOD,
        "combined/method_radar_combined.png",
        left_title="人工评审",
        right_title="多源模型评审",
        ylim_max=0.7,
        legend_ncol=2,
        legend_y=0.01,
    )

    print("\n全部完成！")
