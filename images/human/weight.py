#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

try:
	from scipy.optimize import minimize
except Exception:  # pragma: no cover
	minimize = None


_DIM_MAP = {
	"effectiveness": "有效性",
	"interference": "无干扰性",
	"deployability": "可部署性",
}


def _rank_list_to_scores(ranking_list: list[str]) -> dict[str, float]:
	n = len(ranking_list)
	scores = {}
	for rank, cid in enumerate(ranking_list, start=1):
		scores[cid] = (n - rank) / (n - 1) if n > 1 else 1.0
	return scores


def _normalize_rank_to_score(series: pd.Series) -> pd.Series:
	series = pd.to_numeric(series, errors="coerce")
	max_rank = series.max()
	if pd.notna(max_rank) and max_rank > 1:
		return (max_rank - series) / (max_rank - 1)
	return pd.Series(1.0, index=series.index)


def load_human_scores(human_dir: Path) -> pd.DataFrame:
	result_df = pd.read_csv(human_dir / "result.csv")
	map_df = pd.read_csv(human_dir / "map.csv")
	result_df["ranking"] = result_df["ranking"].apply(json.loads)
	result_df["dimension"] = result_df["dimension"].map(_DIM_MAP).fillna(result_df["dimension"])

	rows = []
	for _, row in result_df.iterrows():
		dim = row["dimension"]
		scores = _rank_list_to_scores(row["ranking"])
		for cid, score in scores.items():
			info = map_df[map_df["候选ID"] == cid].iloc[0]
			rows.append({
				"dimension": dim,
				"generator": info["Profile"],
				"method": info["Method"],
				"score": float(score),
			})

	human = pd.DataFrame(rows)
	human = human.groupby(["dimension", "generator", "method"], as_index=False)["score"].mean()
	return human


def load_llm_scores(analysis_dir: Path) -> pd.DataFrame:
	llm = pd.read_csv(analysis_dir / "analysis_summary_3d.csv")
	llm["dimension"] = llm["dimension"].map(_DIM_MAP).fillna(llm["dimension"])
	llm["score"] = _normalize_rank_to_score(llm["avg_rank"])
	return llm[["judge", "dimension", "generator", "method", "score"]]


def build_training_table(human: pd.DataFrame, llm: pd.DataFrame) -> pd.DataFrame:
	pivot = llm.pivot_table(
		index=["dimension", "generator", "method"],
		columns="judge",
		values="score",
		aggfunc="mean",
	)
	merged = human.merge(
		pivot.reset_index(),
		on=["dimension", "generator", "method"],
		how="inner",
	)
	return merged


def fit_weights(X: np.ndarray, y: np.ndarray) -> np.ndarray:
	n = X.shape[1]
	if minimize is None:
		# fallback: uniform weights
		w = np.ones(n) / n
		return w

	def obj(w):
		return np.mean((X @ w - y) ** 2)

	cons = ({"type": "eq", "fun": lambda w: np.sum(w) - 1.0},)
	bounds = [(0.0, 1.0) for _ in range(n)]
	w0 = np.ones(n) / n
	res = minimize(obj, w0, bounds=bounds, constraints=cons, method="SLSQP")
	if not res.success:
		return w0
	return res.x


def compute_weights(merged: pd.DataFrame, per_dimension: bool) -> pd.DataFrame:
	judge_cols = [c for c in merged.columns if c not in {"dimension", "generator", "method", "score"}]
	rows = []

	if per_dimension:
		for dim, sub in merged.groupby("dimension"):
			X = sub[judge_cols].to_numpy(dtype=float)
			y = sub["score"].to_numpy(dtype=float)
			w = fit_weights(X, y)
			for j, val in zip(judge_cols, w):
				rows.append({"dimension": dim, "judge": j, "weight": float(val)})
	else:
		X = merged[judge_cols].to_numpy(dtype=float)
		y = merged["score"].to_numpy(dtype=float)
		w = fit_weights(X, y)
		for j, val in zip(judge_cols, w):
			rows.append({"dimension": "all", "judge": j, "weight": float(val)})

	return pd.DataFrame(rows)


def apply_weights(merged: pd.DataFrame, weights: pd.DataFrame) -> pd.DataFrame:
	judge_cols = [c for c in merged.columns if c not in {"dimension", "generator", "method", "score"}]

	if (weights["dimension"].nunique() == 1) and (weights["dimension"].iloc[0] == "all"):
		w = weights.set_index("judge")["weight"].reindex(judge_cols).fillna(0.0).to_numpy()
		pred = merged[judge_cols].to_numpy(dtype=float) @ w
		out = merged[["dimension", "generator", "method", "score"]].copy()
		out["pred_score"] = pred
		return out

	# per-dimension weights
	out_rows = []
	for dim, sub in merged.groupby("dimension"):
		w = weights[weights["dimension"] == dim].set_index("judge")["weight"].reindex(judge_cols).fillna(0.0).to_numpy()
		pred = sub[judge_cols].to_numpy(dtype=float) @ w
		part = sub[["dimension", "generator", "method", "score"]].copy()
		part["pred_score"] = pred
		out_rows.append(part)
	return pd.concat(out_rows, ignore_index=True)


def main() -> None:
	p = argparse.ArgumentParser()
	p.add_argument("--human-dir", type=Path, default=Path.cwd())
	p.add_argument("--analysis-dir", type=Path, default=Path.cwd().parents[0] / "analysis")
	p.add_argument("--per-dimension", action="store_true")
	p.add_argument("--out", type=Path, default=Path.cwd())
	args = p.parse_args()

	human = load_human_scores(args.human_dir)
	llm = load_llm_scores(args.analysis_dir)
	merged = build_training_table(human, llm)
	weights = compute_weights(merged, per_dimension=args.per_dimension)
	fitted = apply_weights(merged, weights)

	weights_path = args.out / ("llm_weights_by_dimension.csv" if args.per_dimension else "llm_weights.csv")
	fitted_path = args.out / "llm_weighted_fit.csv"

	weights.to_csv(weights_path, index=False)
	fitted.to_csv(fitted_path, index=False)

	# Print summary
	mse = np.mean((fitted["pred_score"].to_numpy() - fitted["score"].to_numpy()) ** 2)
	print("Weights saved to:", weights_path)
	print("Fitted scores saved to:", fitted_path)
	print("MSE:", float(mse))


if __name__ == "__main__":
	main()
