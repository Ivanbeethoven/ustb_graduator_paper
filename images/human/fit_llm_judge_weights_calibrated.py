#!/usr/bin/env python3
"""Fit per-dimension (or global) weights over LLM judges to best match human review scores.

This script is intentionally standalone (it does not modify existing pipelines).

Compared to the baseline (images/human/weight.py):
- Uses a stable score normalization for LLM avg_rank based on group-wise max_rank.
- Optional per-dimension calibration: y ~= a_d * (X w_d) + b_d.
- Optional train/val split metrics to sanity-check overfitting.

Inputs (auto-detected by default):
- Human: images/human/result.csv + images/human/map.csv
- LLM summary: images/analysis/analysis_summary_3d.csv

Outputs (default to images/human/):
- llm_weights_calibrated.csv (global) or llm_weights_calibrated_by_dimension.csv
- llm_weighted_fit_calibrated.csv (predictions)
- llm_weight_fit_diagnostics.csv (baselines + mse)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

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


def _first_existing(candidates: Iterable[Path]) -> Path | None:
	for p in candidates:
		if p.exists():
			return p
	return None


def _rankings_to_rows(result_df: pd.DataFrame) -> pd.DataFrame:
	rows: list[dict[str, object]] = []
	for _, r in result_df.iterrows():
		ranking = json.loads(r["ranking"]) if isinstance(r["ranking"], str) else r["ranking"]
		n = len(ranking)
		for rank, cid in enumerate(ranking, start=1):
			score = (n - rank) / (n - 1) if n > 1 else 1.0
			rows.append({
				"dimension": r["dimension"],
				"candidate_id": cid,
				"score": float(score),
			})
	return pd.DataFrame(rows)


def load_human_scores(result_csv: Path, map_csv: Path) -> pd.DataFrame:
	result_df = pd.read_csv(result_csv)
	map_df = pd.read_csv(map_csv)

	result_df["dimension"] = result_df["dimension"].map(_DIM_MAP).fillna(result_df["dimension"])

	rank_rows = _rankings_to_rows(result_df)
	merged = rank_rows.merge(map_df, left_on="candidate_id", right_on="候选ID", how="left")
	missing = merged[merged["Profile"].isna()]
	if not missing.empty:
		raise ValueError(
			"Some candidate IDs in result.csv are missing from map.csv. "
			f"Example: {missing['candidate_id'].iloc[0]}"
		)

	human = (
		merged.rename(columns={"Profile": "generator", "Method": "method"})
		.groupby(["dimension", "generator", "method"], as_index=False)["score"]
		.mean()
	)
	return human


def load_llm_scores(
	analysis_csv: Path,
	group_norm_cols: list[str],
) -> pd.DataFrame:
	llm = pd.read_csv(analysis_csv)
	llm["dimension"] = llm["dimension"].map(_DIM_MAP).fillna(llm["dimension"])

	needed = {"judge", "dimension", "generator", "method", "avg_rank", "max_rank"}
	missing = needed - set(llm.columns)
	if missing:
		raise ValueError(f"analysis_summary_3d.csv missing columns: {sorted(missing)}")

	# Use group-wise candidate count N based on max observed `max_rank` in that group.
	# Default grouping is [judge, dimension] so each judge+dimension has its own N.
	group_max = llm.groupby(group_norm_cols, dropna=False)["max_rank"].transform("max")
	N = pd.to_numeric(group_max, errors="coerce")
	avg_rank = pd.to_numeric(llm["avg_rank"], errors="coerce")

	den = (N - 1).where((N - 1) > 0, other=np.nan)
	score = (N - avg_rank) / den
	llm["score"] = score.clip(0.0, 1.0)

	keep = ["judge", "dimension", "generator", "method", "score"]
	if "count" in llm.columns:
		keep.append("count")
	return llm[keep]


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
	if merged.empty:
		raise ValueError(
			"No overlapping rows between human and llm after merge. "
			"Check that dimension/generator/method names match."
		)
	return merged


def _impute_col_mean(X: np.ndarray) -> np.ndarray:
	X2 = X.copy()
	col_means = np.nanmean(X2, axis=0)
	# If a whole column is NaN, fall back to 0.5 (neutral).
	col_means = np.where(np.isfinite(col_means), col_means, 0.5)
	inds = np.where(~np.isfinite(X2))
	X2[inds] = np.take(col_means, inds[1])
	return X2


def _fit_affine(z: np.ndarray, y: np.ndarray, a_nonneg: bool) -> tuple[float, float]:
	"""Closed-form least squares fit for y ~= a*z + b."""
	z = np.asarray(z, dtype=float)
	y = np.asarray(y, dtype=float)
	z_mean = float(np.mean(z))
	y_mean = float(np.mean(y))
	z_centered = z - z_mean
	y_centered = y - y_mean
	var = float(np.mean(z_centered**2))
	if var <= 1e-12:
		a = 0.0
		b = y_mean
		return a, b
	cov = float(np.mean(z_centered * y_centered))
	a = cov / var
	b = y_mean - a * z_mean
	if a_nonneg and a < 0:
		# If the best linear fit would invert the scale, clamp to a=0.
		a = 0.0
		b = y_mean
	return float(a), float(b)


def _mse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
	err = np.asarray(y_pred, dtype=float) - np.asarray(y_true, dtype=float)
	return float(np.mean(err**2))


def fit_weights_one(
	X: np.ndarray,
	y: np.ndarray,
	calibrate: bool,
	a_nonneg: bool,
	l2_to_uniform: float,
	rng: np.random.Generator,
) -> tuple[np.ndarray, float, float]:
	"""Returns (w, a, b). If calibrate=False, returns a=1,b=0."""
	X = _impute_col_mean(X)
	y = np.asarray(y, dtype=float)

	k = X.shape[1]
	w0 = np.ones(k, dtype=float) / k
	uniform = w0.copy()

	def objective(w: np.ndarray) -> float:
		w = np.asarray(w, dtype=float)
		z = X @ w
		if calibrate:
			a, b = _fit_affine(z, y, a_nonneg=a_nonneg)
			pred = a * z + b
		else:
			pred = z
		mse = _mse(y, pred)
		if l2_to_uniform > 0:
			mse += float(l2_to_uniform) * float(np.mean((w - uniform) ** 2))
		return mse

	if minimize is None:
		# Fallback: random restarts around uniform, pick best.
		best_w = w0
		best_obj = objective(best_w)
		for _ in range(64):
			w = rng.random(k)
			w = w / w.sum()
			obj = objective(w)
			if obj < best_obj:
				best_obj = obj
				best_w = w
		w = best_w
	else:
		cons = ({"type": "eq", "fun": lambda w: np.sum(w) - 1.0},)
		bounds = [(0.0, 1.0) for _ in range(k)]
		res = minimize(objective, w0, bounds=bounds, constraints=cons, method="SLSQP")
		w = w0 if (not getattr(res, "success", False)) else np.asarray(res.x, dtype=float)

	z = X @ w
	if calibrate:
		a, b = _fit_affine(z, y, a_nonneg=a_nonneg)
		return w, a, b
	return w, 1.0, 0.0


def _split_train_val(n: int, val_frac: float, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
	idx = np.arange(n)
	rng.shuffle(idx)
	val_n = int(round(n * val_frac))
	val_n = max(0, min(n, val_n))
	val_idx = idx[:val_n]
	train_idx = idx[val_n:]
	return train_idx, val_idx


def main() -> None:
	p = argparse.ArgumentParser()

	p.add_argument("--data-dir", type=Path, default=Path.cwd() / "data")
	p.add_argument("--human-dir", type=Path, default=None)
	p.add_argument("--analysis-csv", type=Path, default=None)
	p.add_argument("--out", type=Path, default=None)

	p.add_argument("--per-dimension", action="store_true")
	p.add_argument("--calibrate", action="store_true", help="Fit y ~= a*(Xw)+b per fitted block")
	p.add_argument("--allow-negative-a", action="store_true", help="Allow a<0 when calibrating")
	p.add_argument("--l2-to-uniform", type=float, default=0.0, help="Regularize weights towards uniform")

	p.add_argument("--val-frac", type=float, default=0.0, help="Holdout fraction for validation (0 disables)")
	p.add_argument("--seed", type=int, default=7)

	p.add_argument(
		"--rank-norm-group",
		nargs="+",
		default=["judge", "dimension"],
		help="Columns to group by when deriving N from max_rank (default: judge dimension)",
	)

	args = p.parse_args()
	rng = np.random.default_rng(args.seed)

	# Resolve inputs.
	# Prefer explicit args; otherwise auto-detect from images/ then data/.
	human_dir = args.human_dir
	if human_dir is None:
		human_dir = _first_existing([
			Path.cwd() / "images" / "human",
			args.data_dir / "human",
		])
		if human_dir is None:
			raise FileNotFoundError("Cannot find human directory (expected images/human or data/human)")

	result_csv = _first_existing([
		human_dir / "result.csv",
		args.data_dir / "result.csv",
		args.data_dir / "human" / "result.csv",
	])
	map_csv = _first_existing([
		human_dir / "map.csv",
		args.data_dir / "map.csv",
		args.data_dir / "human" / "map.csv",
	])
	if result_csv is None or map_csv is None:
		raise FileNotFoundError("Cannot find human result.csv/map.csv")

	analysis_csv = args.analysis_csv
	if analysis_csv is None:
		analysis_csv = _first_existing([
			Path.cwd() / "images" / "analysis" / "analysis_summary_3d.csv",
			args.data_dir / "analysis_summary_3d.csv",
			args.data_dir / "analysis" / "analysis_summary_3d.csv",
		])
		if analysis_csv is None:
			raise FileNotFoundError("Cannot find analysis_summary_3d.csv")

	out_dir = args.out
	if out_dir is None:
		out_dir = _first_existing([
			Path.cwd() / "images" / "human",
			args.data_dir,
		])
		if out_dir is None:
			out_dir = Path.cwd()
	out_dir.mkdir(parents=True, exist_ok=True)

	human = load_human_scores(result_csv, map_csv)
	llm = load_llm_scores(analysis_csv, group_norm_cols=list(args.rank_norm_group))
	merged = build_training_table(human, llm)

	judge_cols = [c for c in merged.columns if c not in {"dimension", "generator", "method", "score"}]
	if not judge_cols:
		raise ValueError("No judge columns found after pivot; check analysis CSV")

	def fit_block(block_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
		X_all = block_df[judge_cols].to_numpy(dtype=float)
		y_all = block_df["score"].to_numpy(dtype=float)

		if args.val_frac > 0:
			train_idx, val_idx = _split_train_val(len(block_df), args.val_frac, rng)
			X_train, y_train = X_all[train_idx], y_all[train_idx]
			X_val, y_val = X_all[val_idx], y_all[val_idx]
		else:
			train_idx = np.arange(len(block_df))
			val_idx = np.array([], dtype=int)
			X_train, y_train = X_all, y_all
			X_val, y_val = X_all[:0], y_all[:0]

		w, a_train, b_train = fit_weights_one(
			X_train,
			y_train,
			calibrate=args.calibrate,
			a_nonneg=(not args.allow_negative_a),
			l2_to_uniform=args.l2_to_uniform,
			rng=rng,
		)

		# Metrics
		z_train = _impute_col_mean(X_train) @ w
		pred_train = (a_train * z_train + b_train) if args.calibrate else z_train
		train_mse = _mse(y_train, pred_train)

		if len(val_idx) > 0:
			z_val = _impute_col_mean(X_val) @ w
			pred_val = (a_train * z_val + b_train) if args.calibrate else z_val
			val_mse = _mse(y_val, pred_val)
		else:
			val_mse = float("nan")

		# Per-sample predictions (on all rows)
		z_all = _impute_col_mean(X_all) @ w
		if args.calibrate:
			# Refit (a,b) on all rows for a more stable final predictor.
			a_all, b_all = _fit_affine(z_all, y_all, a_nonneg=(not args.allow_negative_a))
			pred_all = a_all * z_all + b_all
			all_mse = _mse(y_all, pred_all)
		else:
			a_all, b_all = 1.0, 0.0
			pred_all = z_all
			all_mse = _mse(y_all, pred_all)
		pred_df = block_df[["dimension", "generator", "method", "score"]].copy()
		pred_df["pred_score"] = pred_all

		weights_df = pd.DataFrame({
			"judge": judge_cols,
			"weight": w,
		})
		weights_df["a"] = float(a_all)
		weights_df["b"] = float(b_all)
		weights_df["a_train"] = float(a_train)
		weights_df["b_train"] = float(b_train)
		weights_df["all_mse"] = float(all_mse)
		weights_df["train_mse"] = float(train_mse)
		weights_df["val_mse"] = float(val_mse)
		weights_df["n_train"] = int(len(train_idx))
		weights_df["n_val"] = int(len(val_idx))
		return weights_df, pred_df

	weight_rows: list[pd.DataFrame] = []
	pred_rows: list[pd.DataFrame] = []
	diag_rows: list[dict[str, object]] = []

	if args.per_dimension:
		for dim, sub in merged.groupby("dimension"):
			w_df, p_df = fit_block(sub)
			w_df.insert(0, "dimension", dim)
			weight_rows.append(w_df)
			pred_rows.append(p_df)

			# Baselines (fit/eval on all rows of the dimension): each single judge, uniform, fitted
			X = _impute_col_mean(sub[judge_cols].to_numpy(dtype=float))
			y = sub["score"].to_numpy(dtype=float)
			uniform = np.ones(len(judge_cols)) / len(judge_cols)
			z_u = X @ uniform
			if args.calibrate:
				a_u, b_u = _fit_affine(z_u, y, a_nonneg=(not args.allow_negative_a))
				mse_u = _mse(y, a_u * z_u + b_u)
			else:
				mse_u = _mse(y, z_u)

			best_w = w_df.set_index("judge")["weight"].reindex(judge_cols).to_numpy(dtype=float)
			z_f = X @ best_w
			if args.calibrate:
				a_f = float(w_df["a"].iloc[0])
				b_f = float(w_df["b"].iloc[0])
				mse_f = _mse(y, a_f * z_f + b_f)
			else:
				mse_f = _mse(y, z_f)

			diag_rows.append({"dimension": dim, "model": "uniform", "mse": float(mse_u)})
			diag_rows.append({"dimension": dim, "model": "fitted", "mse": float(mse_f)})
			for j_i, j in enumerate(judge_cols):
				z_j = X[:, j_i]
				if args.calibrate:
					a_j, b_j = _fit_affine(z_j, y, a_nonneg=(not args.allow_negative_a))
					mse_j = _mse(y, a_j * z_j + b_j)
				else:
					mse_j = _mse(y, z_j)
				diag_rows.append({"dimension": dim, "model": f"single:{j}", "mse": float(mse_j)})
	else:
		w_df, p_df = fit_block(merged)
		w_df.insert(0, "dimension", "all")
		weight_rows.append(w_df)
		pred_rows.append(p_df)

	weights = pd.concat(weight_rows, ignore_index=True)
	pred = pd.concat(pred_rows, ignore_index=True)
	diag = pd.DataFrame(diag_rows)

	if args.per_dimension:
		weights_path = out_dir / "llm_weights_calibrated_by_dimension.csv"
	else:
		weights_path = out_dir / "llm_weights_calibrated.csv"
	pred_path = out_dir / "llm_weighted_fit_calibrated.csv"
	diag_path = out_dir / "llm_weight_fit_diagnostics.csv"

	weights.to_csv(weights_path, index=False)
	pred.to_csv(pred_path, index=False)
	if not diag.empty:
		diag.to_csv(diag_path, index=False)

	mse_all = _mse(pred["score"].to_numpy(dtype=float), pred["pred_score"].to_numpy(dtype=float))
	print("Weights saved to:", weights_path)
	print("Fitted scores saved to:", pred_path)
	if not diag.empty:
		print("Diagnostics saved to:", diag_path)
	print("MSE (all rows):", float(mse_all))


if __name__ == "__main__":
	main()
