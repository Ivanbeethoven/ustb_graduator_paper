#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pandas", "matplotlib", "seaborn", "numpy"]
# ///
"""
统一绘制四个雷达图：
  (a) 生成模型对比（人工评审）
  (b) 生成模型对比（LLM评审）
  (c) 方法配置对比（人工评审）
  (d) 方法配置对比（LLM评审）
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
# 硬编码数据（从原始脚本提取）
# 维度顺序：有效性、无干扰性、可部署性
# ============================================================
DIMS = ["有效性", "无干扰性", "可部署性"]

# --- (a) 人工评审 - 生成模型 ---
HUMAN_GENERATOR = {
    "Qwen3":     [0.250957, 0.366071, 0.293233],
    "DeepSeek":  [0.614923, 0.613252, 0.607143],
    "GLM-4.5":   [0.536432, 0.465461, 0.520912],
    "GPT-5":     [0.645337, 0.595630, 0.654135],
    "Grok4":     [0.450945, 0.459586, 0.424577],
}

# --- (b) LLM评审 - 生成模型 ---
LLM_GENERATOR = {
    "ali-qwen":  [0.346037, 0.534086, 0.576198],
    "deepseek":  [0.419500, 0.592381, 0.679724],
    "glm4.5":    [0.454759, 0.452186, 0.461588],
    "gpt5":      [0.848931, 0.331681, 0.189577],
    "grok4":     [0.308402, 0.466735, 0.469852],
}

# --- (c) 人工评审 - 方法配置 ---
HUMAN_METHOD = {
    "KPEDefense":              [0.674279, 0.599060, 0.656015],
    "KPEDefense w/o COT":      [0.476138, 0.425752, 0.420301],
    "KPEDefense w/o Feedback": [0.397368, 0.375376, 0.381203],
    "KPEDefense w/o RAG":      [0.452611, 0.599812, 0.542481],
}

# --- (d) LLM评审 - 方法配置 ---
LLM_METHOD = {
    "KPEDefense":              [0.660557, 0.539050, 0.516508],
    "KPEDefense w/o COT":      [0.379133, 0.465507, 0.512104],
    "KPEDefense w/o Feedback": [0.287396, 0.407509, 0.423107],
    "KPEDefense w/o RAG":      [0.575102, 0.489736, 0.450068],
}

# LLM generator display labels
LLM_GEN_LABELS = {
    "ali-qwen": "ali-qwen",
    "deepseek": "deepseek",
    "glm4.5":   "glm4.5",
    "gpt5":     "gpt5",
    "grok4":    "grok4",
}

# ============================================================
# 绘图参数
# ============================================================
FIGSIZE = (6.4, 6.4)
DIM_LABEL_SIZE = 13
RING_LABEL_SIZE = 10
LEGEND_SIZE = 11
LINE_WIDTH = 2.8
FILL_ALPHA = 0.15

LABEL_POSITIONS = {
    "有效性":   (0.50, 1.02),
    "无干扰性": (1.00, 0.22),
    "可部署性": (0.00, 0.22),
}


def draw_radar(
    data: dict[str, list[float]],
    filename: str,
    ylim_max: float = 0.7,
    yticks: list[float] | None = None,
    legend_anchor: tuple[float, float] = (1.24, 1.08),
    legend_loc: str = "upper right",
    legend_fs: int | None = None,
    legend_ncol: int = 1,
    legend_bbox_transform=None,
) -> None:
    angles = np.linspace(0, 2 * np.pi, len(DIMS), endpoint=False).tolist()
    angles += angles[:1]

    palette = sns.color_palette("husl", n_colors=len(data))

    fig = plt.figure(figsize=FIGSIZE)
    ax = fig.add_subplot(111, polar=True)
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

    for (name, values), color in zip(data.items(), palette):
        vals = list(values) + [values[0]]
        ax.plot(angles, vals, color=color, linewidth=LINE_WIDTH, label=name)
        ax.fill(angles, vals, color=color, alpha=FILL_ALPHA)

    ax.set_title("")
    fs = legend_fs if legend_fs is not None else LEGEND_SIZE
    ax.legend(loc=legend_loc, bbox_to_anchor=legend_anchor,
              frameon=False, fontsize=fs, ncol=legend_ncol)
    plt.tight_layout(pad=0.8)
    out_path = OUT_DIR / filename
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"✓ {out_path}")


if __name__ == "__main__":
    # (a) 人工评审 - 生成模型
    draw_radar(
        HUMAN_GENERATOR,
        "human/analysis/human_generator_radar_overall.png",
        ylim_max=0.7,
    )
    # (b) LLM评审 - 生成模型
    draw_radar(
        LLM_GENERATOR,
        "analysis/plots/summary/radar_generator_overall.png",
        ylim_max=0.7,  # 原始 ylim=0.7
    )
    # (c) 人工评审 - 方法配置
    draw_radar(
        HUMAN_METHOD,
        "human/analysis/human_method_radar_overall.png",
        ylim_max=0.7,
        legend_loc="lower center",
        legend_anchor=(0.5, 1.08),
        legend_fs=12,
        legend_ncol=2,
    )
    # (d) LLM评审 - 方法配置
    draw_radar(
        LLM_METHOD,
        "analysis/plots/summary/radar_method_overall-1.png",
        ylim_max=0.7,
        legend_loc="lower center",
        legend_anchor=(0.5, 1.08),
        legend_fs=12,
        legend_ncol=2,
    )
    print("\n全部完成！")
