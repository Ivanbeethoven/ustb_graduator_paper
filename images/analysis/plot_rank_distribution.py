#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Any, Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Prefer grayscale fonts and clean style
plt.rcParams.update(
    {
        "figure.dpi": 150,
        "savefig.dpi": 200,
        "axes.unicode_minus": False,
        "font.size": 10,
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

DIMENSIONS = ["有效性", "无干扰性", "可部署性"]


def load_anonymization(run_dir: Path) -> Dict[str, Any]:
    path = run_dir / "anonymization_map.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def iter_judge_results(run_dir: Path) -> Iterable[tuple[str, str, Dict[str, Any]]]:
    for judge_folder in run_dir.iterdir():
        if not judge_folder.is_dir():
            continue
        if judge_folder.name.startswith("."):
            continue
        for file in judge_folder.glob("*.json"):
            if file.name in ("cost_summary.json", "anonymization_map.json"):
                continue
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
            except Exception:
                continue
            yield judge_folder.name, file.name, data


def _safe_label(name: str) -> str:
    if name is None:
        return ""
    s = str(name)
    if s.startswith("no_"):
        return "w/o " + s[3:].replace("_", " ")
    return s.replace("_", " ")


def _bw_palette(n: int) -> list[str]:
    if n <= 1:
        return ["#404040"]
    # darker shades for smaller ranks
    shades = np.linspace(0.20, 0.80, n)
    return [plt.cm.Greys_r(s) for s in shades]


def _rank_bucket(rank: int) -> str:
    return str(rank)


def _make_distribution_table(
    counts: Counter, totals: Dict[tuple[str, str], int]
) -> pd.DataFrame:
    rows = []
    for (dim, key, rank), cnt in counts.items():
        bucket = _rank_bucket(rank)
        total = totals.get((dim, key), 0)
        rows.append(
            {
                "dimension": dim,
                "key": key,
                "rank_bucket": bucket,
                "count": cnt,
                "total": total,
                "ratio": (cnt / total) if total else 0.0,
            }
        )
    if not rows:
        return pd.DataFrame(columns=["dimension", "key", "rank_bucket", "count", "total", "ratio"])
    df = pd.DataFrame(rows)
    # aggregate into buckets (merge >k when top_k is set)
    df = (
        df.groupby(["dimension", "key", "rank_bucket"], as_index=False)
        .agg({"count": "sum", "total": "max"})
    )
    df["ratio"] = df.apply(lambda r: (r["count"] / r["total"]) if r["total"] else 0.0, axis=1)
    return df


def _plot_stacked_bar(
    df: pd.DataFrame,
    out_path: Path,
    title: str,
    xlabel: str,
):
    if df.empty:
        return
    order = sorted(df["key"].unique())
    rank_order = sorted(df["rank_bucket"].unique(), key=lambda x: int(str(x)))
    pivot = (
        df.pivot_table(index="key", columns="rank_bucket", values="ratio", aggfunc="sum")
        .reindex(index=order, columns=rank_order, fill_value=0.0)
    )
    pivot.index = [_safe_label(k) for k in pivot.index]
    colors = _bw_palette(len(pivot.columns))
    ax = pivot.plot(kind="bar", stacked=True, figsize=(11.2, 4.8), color=colors, width=0.7)
    ax.set_title(title, fontsize=13, pad=12)
    ax.set_ylabel("比例", fontsize=11)
    ax.set_xlabel(xlabel, fontsize=11)
    ax.tick_params(axis="x", labelrotation=0)
    ax.set_ylim(0, 1.0)
    ax.grid(axis="y", alpha=0.9)
    for spine_name, spine in ax.spines.items():
        if spine_name in {"top", "right"}:
            spine.set_visible(False)
        else:
            spine.set_color("#2A2A2A")
            spine.set_linewidth(0.8)
    leg = ax.get_legend()
    if leg is not None:
        leg.set_title("排名")
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=200)
    plt.close()


def main() -> None:
    p = argparse.ArgumentParser(description="Plot ordinal rank distributions (black/white).")
    p.add_argument("--run-dir", type=Path, default=Path.cwd() / "v_test_run", help="评审结果目录")
    p.add_argument("--out-dir", type=Path, default=Path.cwd() / "analysis" / "output_rank", help="输出目录")
    p.add_argument("--dimensions", nargs="*", default=None, help="只绘制指定维度")
    args = p.parse_args()

    anon = load_anonymization(args.run_dir)
    candidates_map: Dict[str, Dict[str, Dict[str, str]]] = anon.get("candidates", {})

    # build candidate_id -> meta map (method/profile)
    cid_to_meta: Dict[str, Dict[str, str]] = {}
    for _cve, cid_map in candidates_map.items():
        for cid, meta in cid_map.items():
            cid_to_meta[cid] = meta

    method_counts: Counter = Counter()
    profile_counts: Counter = Counter()
    method_totals: Dict[tuple[str, str], int] = defaultdict(int)
    profile_totals: Dict[tuple[str, str], int] = defaultdict(int)

    for _judge_alias, _fname, data in iter_judge_results(args.run_dir):
        parsed_obj = data.get("judge", {}).get("parsed") or data.get("parsed") or {}
        rankings = parsed_obj.get("rankings", {}) if isinstance(parsed_obj, dict) else {}
        for dim in DIMENSIONS:
            dim_list = rankings.get(dim)
            if not dim_list and isinstance(parsed_obj, dict):
                dim_list = parsed_obj.get(dim)
            if not dim_list:
                continue
            for item in dim_list:
                cid = item.get("candidate_id")
                rank = item.get("rank")
                if not cid or not isinstance(rank, int):
                    continue
                meta = cid_to_meta.get(cid, {})
                method = meta.get("method") or "unknown"
                profile = meta.get("profile") or "unknown"
                method_counts[(dim, method, rank)] += 1
                profile_counts[(dim, profile, rank)] += 1
                method_totals[(dim, method)] += 1
                profile_totals[(dim, profile)] += 1

    dims = args.dimensions or DIMENSIONS

    method_df = _make_distribution_table(method_counts, method_totals)
    profile_df = _make_distribution_table(profile_counts, profile_totals)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    if not method_df.empty:
        method_df.to_csv(args.out_dir / "rank_distribution_method.csv", index=False)
    if not profile_df.empty:
        profile_df.to_csv(args.out_dir / "rank_distribution_profile.csv", index=False)

    for dim in dims:
        msub = method_df[method_df["dimension"] == dim]
        psub = profile_df[profile_df["dimension"] == dim]
        _plot_stacked_bar(
            msub,
            args.out_dir / "plots" / dim / "method_rank_distribution_full.png",
            title=f"排名分布（方法）｜维度：{dim}｜完整位次",
            xlabel="方法",
        )
        _plot_stacked_bar(
            psub,
            args.out_dir / "plots" / dim / "profile_rank_distribution_full.png",
            title=f"排名分布（生成模型）｜维度：{dim}｜完整位次",
            xlabel="生成模型",
        )

    print(f"[ok] output to {args.out_dir}")


if __name__ == "__main__":
    main()
