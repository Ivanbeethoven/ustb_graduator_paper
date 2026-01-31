#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
import subprocess
import sys
from collections import defaultdict, Counter

RUN_DIR = Path.cwd() / "v_test_run"
THIS_DIR = Path(__file__).resolve().parent
DIMENSIONS = ["有效性", "无干扰性", "可部署性"]


def load_anonymization(run_dir: Path) -> Dict[str, Any]:
    path = run_dir / "anonymization_map.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def iter_judge_results(run_dir: Path):
    for judge_folder in run_dir.iterdir():
        if not judge_folder.is_dir():
            continue
        # skip known metadata files
        if judge_folder.name.startswith("."):
            continue
        for file in judge_folder.glob("*.json"):
            # skip cost summary etc
            if file.name in ("cost_summary.json",):
                continue
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
            except Exception:
                continue
            yield judge_folder.name, file.name, data


def analyze(run_dir: Path, out_dir: Path, run_plots: bool = True, single_dims: List[str] | None = None):
    anon = load_anonymization(run_dir)
    candidates_map: Dict[str, Dict[str, Dict[str, str]]] = anon.get("candidates", {})
    # candidate_map: {cve: {cid: {method, profile, source}}}

    # Structures to accumulate
    # per-judge -> dimension -> candidate -> list of ranks
    judge_dim_candidate_ranks: Dict[str, Dict[str, Dict[str, List[int]]]] = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    # per-judge counts
    judge_counts: Dict[str, int] = Counter()

    # judge_profiles mapping: alias -> actual profile name
    anon_judge_profiles = anon.get("judge_profiles", {}) if isinstance(anon, dict) else {}

    for judge_alias, fname, data in iter_judge_results(run_dir):
        # skip if this is anonymization_map file
        if fname == "anonymization_map.json":
            continue
        parsed = data.get("judge", {})
        # map alias to actual model name when available
        actual_judge = anon_judge_profiles.get(judge_alias, judge_alias)
        profile = parsed.get("profile") or actual_judge
        rankings = data.get("judge", {}).get("parsed") or data.get("judge", {}).get("parsed")
        # if parsed missing try top-level parsed
        parsed_obj = data.get("judge", {}).get("parsed")
        if not parsed_obj:
            # sometimes parsed is top-level
            parsed_obj = data.get("parsed") or {}
        # parsed_obj expected to contain rankings -> dimension lists with rank/candidate_id
        for dim in DIMENSIONS:
            dim_list = parsed_obj.get("rankings", {}).get(dim) if isinstance(parsed_obj, dict) else None
            if not dim_list:
                # try direct keys
                dim_list = parsed_obj.get(dim) if isinstance(parsed_obj, dict) else None
            if not dim_list:
                continue
            # create map candidate->rank
            for item in dim_list:
                cid = item.get("candidate_id")
                rank = item.get("rank")
                if cid and isinstance(rank, int):
                    judge_dim_candidate_ranks[actual_judge][dim][cid].append(rank)
        judge_counts[actual_judge] += 1

    # aggregate per method/profile across all judges
    method_stats = defaultdict(lambda: defaultdict(list))  # method -> dim -> ranks
    profile_stats = defaultdict(lambda: defaultdict(list))

    # walk judge_dim_candidate_ranks and map candidate ids to method/profile using candidates_map
    for cve_id, cid_map in candidates_map.items():
        for cid, meta in cid_map.items():
            method = meta.get("method")
            profile = meta.get("profile")
            # collect ranks across judges/dims
            for judge_alias, dims in judge_dim_candidate_ranks.items():
                for dim, cmap in dims.items():
                    ranks = cmap.get(cid) or []
                    for r in ranks:
                        method_stats[method][dim].append(r)
                        profile_stats[profile][dim].append(r)

    # aggregate per-judge stats (per judge -> per method/profile)
    per_judge_method = {}
    per_judge_profile = {}
    for judge_alias, dims in judge_dim_candidate_ranks.items():
        jm = defaultdict(lambda: defaultdict(list))
        jp = defaultdict(lambda: defaultdict(list))
        # for each cve, find candidates for that cve
        for cve_id, cid_map in candidates_map.items():
            for cid, meta in cid_map.items():
                method = meta.get("method")
                profile = meta.get("profile")
                for dim, cmap in dims.items():
                    ranks = cmap.get(cid) or []
                    for r in ranks:
                        jm[method][dim].append(r)
                        jp[profile][dim].append(r)
        per_judge_method[judge_alias] = jm
        per_judge_profile[judge_alias] = jp

    # summarize
    def _metric_record(ranks: List[int]):
        if not ranks:
            return {
                "count": 0,
                "avg_rank": None,
                "first_count": 0,
                "min_rank": None,
                "max_rank": None,
                "var_rank": None,
            }
        count = len(ranks)
        avg = sum(ranks) / count
        first_count = sum(1 for x in ranks if x == 1)
        min_rank = min(ranks)
        max_rank = max(ranks)
        var_rank = sum((r - avg) ** 2 for r in ranks) / count
        return {
            "count": count,
            "avg_rank": avg,
            "first_count": first_count,
            "min_rank": min_rank,
            "max_rank": max_rank,
            "var_rank": var_rank,
        }

    metric_columns = ["count", "avg_rank", "first_count", "min_rank", "max_rank", "var_rank"]

    def _metric_row(metrics: Dict[str, Any]) -> List[Any]:
        return [metrics.get(col) for col in metric_columns]

    def summarize(stats: Dict[str, Dict[str, List[int]]]):
        out = {}
        for key, dims in stats.items():
            out[key] = {}
            for dim, ranks in dims.items():
                out[key][dim] = _metric_record(ranks)
        return out

    # convert defaultdicts to plain dicts for summarize/serialization
    def _to_plain(d):
        return {k: dict(v) for k, v in d.items()}

    summary = {
        "per_method": summarize(_to_plain(method_stats)),
        "per_profile": summarize(_to_plain(profile_stats)),
        "per_judge": {},
        "judge_counts": dict(judge_counts),
    }

    # add per-judge summaries
    for judge_alias, jm in per_judge_method.items():
        summary["per_judge"][judge_alias] = {
            "per_method": summarize({k: dict(v) for k, v in jm.items()}),
            "per_profile": summarize({k: dict(v) for k, v in per_judge_profile.get(judge_alias, {}).items()}),
        }

    # 三维聚合：评测 LLM (judge) x 生成 LLM (generator/profile) x 方法
    # structure: judge -> generator_profile -> method -> dim -> list[ranks]
    agg_3d = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list))))
    for cve_id, cid_map in candidates_map.items():
        for cid, meta in cid_map.items():
            gen_profile = meta.get("profile")
            method = meta.get("method")
            for judge_alias, dims in judge_dim_candidate_ranks.items():
                for dim, cmap in dims.items():
                    ranks = cmap.get(cid) or []
                    for r in ranks:
                        agg_3d[judge_alias][gen_profile][method][dim].append(r)

    # convert agg_3d to serializable summary: counts/avg/first
    per_judge_gen_method = {}
    for judge_alias, gen_map in agg_3d.items():
        per_judge_gen_method[judge_alias] = {}
        for gen_profile, method_map in gen_map.items():
            per_judge_gen_method[judge_alias].setdefault(gen_profile, {})
            for method, dim_map in method_map.items():
                per_judge_gen_method[judge_alias][gen_profile][method] = {}
                for dim, ranks in dim_map.items():
                    per_judge_gen_method[judge_alias][gen_profile][method][dim] = _metric_record(ranks)

    summary["per_judge_by_generator_by_method"] = per_judge_gen_method

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "analysis_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    # write simple CSV
    lines = ["type,key,dimension," + ",".join(metric_columns)]
    for tname, table in (("method", summary["per_method"]), ("profile", summary["per_profile"])):
        for key, dims in table.items():
            for dim, metrics in dims.items():
                row = [tname, key, dim, *_metric_row(metrics)]
                lines.append(",".join("" if v is None else str(v) for v in row))
    (out_dir / "analysis_summary.csv").write_text("\n".join(lines), encoding="utf-8")

    # write per-judge CSV
    judge_lines = ["judge,type,key,dimension," + ",".join(metric_columns)]
    for judge_alias, stats in summary.get("per_judge", {}).items():
        # methods
        for key, dims in stats.get("per_method", {}).items():
            for dim, metrics in dims.items():
                row = [judge_alias, "method", key, dim, *_metric_row(metrics)]
                judge_lines.append(",".join("" if v is None else str(v) for v in row))
        # profiles
        for key, dims in stats.get("per_profile", {}).items():
            for dim, metrics in dims.items():
                row = [judge_alias, "profile", key, dim, *_metric_row(metrics)]
                judge_lines.append(",".join("" if v is None else str(v) for v in row))
    (out_dir / "analysis_summary_by_judge.csv").write_text("\n".join(judge_lines), encoding="utf-8")

    # write 3D CSV: judge,generator,method,dimension,count,avg_rank,first_count
    csv3_lines = ["judge,generator,method,dimension," + ",".join(metric_columns)]
    for judge_alias, gen_map in summary.get("per_judge_by_generator_by_method", {}).items():
        for gen_profile, methods in gen_map.items():
            for method, dims in methods.items():
                for dim, metrics in dims.items():
                    row = [judge_alias, gen_profile, method, dim, *_metric_row(metrics)]
                    csv3_lines.append(",".join("" if v is None else str(v) for v in row))
    (out_dir / "analysis_summary_3d.csv").write_text("\n".join(csv3_lines), encoding="utf-8")

    # 单一维度 CSV 输出，方便单独分析与绘图
    for dim in DIMENSIONS:
        dim_lines = ["type,key," + ",".join(metric_columns)]
        for tname, table in (("method", summary["per_method"]), ("profile", summary["per_profile"])):
            for key, dims in table.items():
                metrics = dims.get(dim) or _metric_record([])
                row = [tname, key, *_metric_row(metrics)]
                dim_lines.append(",".join("" if v is None else str(v) for v in row))
        (out_dir / f"analysis_summary_{dim}.csv").write_text("\n".join(dim_lines), encoding="utf-8")

        # per-judge dim CSV
        judge_dim_lines = ["judge,type,key," + ",".join(metric_columns)]
        for judge_alias, stats in summary.get("per_judge", {}).items():
            for tname in ("per_method", "per_profile"):
                table = stats.get(tname, {})
                typ = "method" if tname == "per_method" else "profile"
                for key, dims in table.items():
                    metrics = dims.get(dim) or _metric_record([])
                    row = [judge_alias, typ, key, *_metric_row(metrics)]
                    judge_dim_lines.append(",".join("" if v is None else str(v) for v in row))
        (out_dir / f"analysis_summary_by_judge_{dim}.csv").write_text("\n".join(judge_dim_lines), encoding="utf-8")

        # 3D per-dim CSV
        csv3_dim_lines = ["judge,generator,method," + ",".join(metric_columns)]
        for judge_alias, gen_map in summary.get("per_judge_by_generator_by_method", {}).items():
            for gen_profile, methods in gen_map.items():
                for method, dims in methods.items():
                    metrics = dims.get(dim) or _metric_record([])
                    row = [judge_alias, gen_profile, method, *_metric_row(metrics)]
                    csv3_dim_lines.append(",".join("" if v is None else str(v) for v in row))
        (out_dir / f"analysis_summary_3d_{dim}.csv").write_text("\n".join(csv3_dim_lines), encoding="utf-8")
    print(f"wrote analysis_summary.json and CSV to {out_dir}")

    # optionally call the plotting script to generate PNGs
    if run_plots:
        plot_script = Path(__file__).resolve().parent / "plot.py"
        if plot_script.exists():
            try:
                cmd = [sys.executable or "python3", str(plot_script), "--out-dir", str(out_dir)]
                if single_dims:
                    cmd.append("--single-dim")
                    cmd.extend(single_dims)
                print(f"[info] running plotting: {' '.join(cmd)}")
                subprocess.run(cmd, check=True)
                print(f"[info] plots generated under {out_dir / 'plots'}")
            except subprocess.CalledProcessError as exc:
                print(f"[warn] plotting failed: {exc}")
        else:
            print(f"[warn] plotting script not found: {plot_script}")


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--run-dir", type=Path, default=RUN_DIR, help="输入评审结果目录，默认 ./v_test_run")
    p.add_argument("--out-dir", type=Path, default=THIS_DIR, help="分析输出目录（默认 analysis 文件夹）")
    p.add_argument("--no-plot", action="store_true", help="仅生成 CSV/JSON，不绘图")
    p.add_argument("--single-dim", nargs="*", default=None, help="只生成单维度的图，传入维度名列表，例如 --single-dim 有效性 可部署性")
    args = p.parse_args()
    analyze(args.run_dir, args.out_dir, run_plots=not args.no_plot, single_dims=args.single_dim)
