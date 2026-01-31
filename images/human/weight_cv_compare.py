#!/usr/bin/env python3
"""Compare baseline vs calibrated judge-weight fitting with simple CV.

Runs:
- Baseline model: convex weights only, using images/human/weight.py logic.
- Calibrated model: convex weights + affine calibration y ~= a*(Xw)+b,
  using images/human/fit_llm_judge_weights_calibrated.py logic.

Outputs:
- images/human/weights_baseline/*
- images/human/weights_calibrated/*
- images/human/weights_cv/cv_summary.csv

Example:
  uv run python images/human/weight_cv_compare.py --cv loo
  uv run python images/human/weight_cv_compare.py --cv kfold --k 5 --seed 7
"""

from __future__ import annotations

import argparse
from pathlib import Path
import importlib.util
import sys

import numpy as np
import pandas as pd

def _load_module(module_name: str, file_path: Path):
	if not file_path.exists():
		raise FileNotFoundError(str(file_path))
	spec = importlib.util.spec_from_file_location(module_name, str(file_path))
	if spec is None or spec.loader is None:
		raise ImportError(f"Cannot load module {module_name} from {file_path}")
	mod = importlib.util.module_from_spec(spec)
	sys.modules[module_name] = mod
	spec.loader.exec_module(mod)
	return mod


ROOT = Path(__file__).resolve().parents[2]
baseline = _load_module("_baseline_weight", ROOT / "images" / "human" / "weight.py")
calibrated = _load_module(
	"_calibrated_weight",
	ROOT / "images" / "human" / "fit_llm_judge_weights_calibrated.py",
)


def _impute_col_mean(X: np.ndarray) -> np.ndarray:
	X2 = X.copy()
	col_means = np.nanmean(X2, axis=0)
	col_means = np.where(np.isfinite(col_means), col_means, 0.5)
	inds = np.where(~np.isfinite(X2))
	X2[inds] = np.take(col_means, inds[1])
	return X2


def _mse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
	err = np.asarray(y_pred, dtype=float) - np.asarray(y_true, dtype=float)
	return float(np.mean(err**2))


def _split_kfold(n: int, k: int, rng: np.random.Generator) -> list[np.ndarray]:
	idx = np.arange(n)
	rng.shuffle(idx)
	return [a for a in np.array_split(idx, k) if len(a) > 0]


def cv_predict_baseline(
	merged: pd.DataFrame,
	per_dimension: bool,
	cv: str,
	k: int,
	seed: int,
) -> pd.DataFrame:
	rng = np.random.default_rng(seed)
	judge_cols = [c for c in merged.columns if c not in {"dimension", "generator", "method", "score"}]

	rows: list[dict[str, object]] = []

	groups = merged.groupby("dimension") if per_dimension else [("all", merged)]
	for dim, sub in groups:
		X = sub[judge_cols].to_numpy(dtype=float)
		X = _impute_col_mean(X)
		y = sub["score"].to_numpy(dtype=float)

		if cv == "loo":
			for i in range(len(sub)):
				train_mask = np.ones(len(sub), dtype=bool)
				train_mask[i] = False
				w = baseline.fit_weights(X[train_mask], y[train_mask])
				pred = float(X[i] @ w)
				rows.append({
					"model": "baseline",
					"dimension": dim,
					"index": int(sub.index[i]),
					"y": float(y[i]),
					"y_pred": pred,
				})
		elif cv == "kfold":
			folds = _split_kfold(len(sub), k=k, rng=rng)
			for fold_id, val_idx in enumerate(folds):
				train_mask = np.ones(len(sub), dtype=bool)
				train_mask[val_idx] = False
				w = baseline.fit_weights(X[train_mask], y[train_mask])
				preds = X[val_idx] @ w
				for local_i, pred in zip(val_idx, preds):
					rows.append({
						"model": "baseline",
						"dimension": dim,
						"fold": int(fold_id),
						"index": int(sub.index[local_i]),
						"y": float(y[local_i]),
						"y_pred": float(pred),
					})
		else:
			raise ValueError("cv must be one of: loo, kfold")

	return pd.DataFrame(rows)


def cv_predict_calibrated(
	merged: pd.DataFrame,
	per_dimension: bool,
	cv: str,
	k: int,
	seed: int,
	l2_to_uniform: float,
	a_nonneg: bool,
) -> pd.DataFrame:
	rng = np.random.default_rng(seed)
	judge_cols = [c for c in merged.columns if c not in {"dimension", "generator", "method", "score"}]

	rows: list[dict[str, object]] = []

	groups = merged.groupby("dimension") if per_dimension else [("all", merged)]
	for dim, sub in groups:
		X = sub[judge_cols].to_numpy(dtype=float)
		X = _impute_col_mean(X)
		y = sub["score"].to_numpy(dtype=float)

		if cv == "loo":
			for i in range(len(sub)):
				train_mask = np.ones(len(sub), dtype=bool)
				train_mask[i] = False
				w, a, b = calibrated.fit_weights_one(
					X[train_mask],
					y[train_mask],
					calibrate=True,
					a_nonneg=a_nonneg,
					l2_to_uniform=l2_to_uniform,
					rng=rng,
				)
				z = float(X[i] @ w)
				pred = float(a * z + b)
				rows.append({
					"model": "calibrated",
					"dimension": dim,
					"index": int(sub.index[i]),
					"y": float(y[i]),
					"y_pred": pred,
					"a": float(a),
					"b": float(b),
				})
		elif cv == "kfold":
			folds = _split_kfold(len(sub), k=k, rng=rng)
			for fold_id, val_idx in enumerate(folds):
				train_mask = np.ones(len(sub), dtype=bool)
				train_mask[val_idx] = False
				w, a, b = calibrated.fit_weights_one(
					X[train_mask],
					y[train_mask],
					calibrate=True,
					a_nonneg=a_nonneg,
					l2_to_uniform=l2_to_uniform,
					rng=rng,
				)
				z = X[val_idx] @ w
				preds = a * z + b
				for local_i, pred in zip(val_idx, preds):
					rows.append({
						"model": "calibrated",
						"dimension": dim,
						"fold": int(fold_id),
						"index": int(sub.index[local_i]),
						"y": float(y[local_i]),
						"y_pred": float(pred),
						"a": float(a),
						"b": float(b),
					})
		else:
			raise ValueError("cv must be one of: loo, kfold")

	return pd.DataFrame(rows)


def _summarize(pred: pd.DataFrame) -> pd.DataFrame:
	out_rows: list[dict[str, object]] = []
	for (model, dim), sub in pred.groupby(["model", "dimension"], dropna=False):
		out_rows.append({
			"model": model,
			"dimension": dim,
			"n": int(len(sub)),
			"mse": _mse(sub["y"].to_numpy(), sub["y_pred"].to_numpy()),
		})

	# Overall (weighted by n)
	df = pd.DataFrame(out_rows)
	overall_rows: list[dict[str, object]] = []
	for model, g in df.groupby("model", dropna=False):
		n_total = float(g["n"].sum())
		mse_weighted = float(np.average(g["mse"].to_numpy(dtype=float), weights=g["n"].to_numpy(dtype=float)))
		overall_rows.append({"model": model, "n": int(n_total), "mse": mse_weighted, "dimension": "__overall__"})
	overall = pd.DataFrame(overall_rows)
	overall["dimension"] = "__overall__"
	return pd.concat([pd.DataFrame(out_rows), overall], ignore_index=True)


def main() -> None:
	p = argparse.ArgumentParser()
	p.add_argument("--cv", choices=["loo", "kfold"], default="loo")
	p.add_argument("--k", type=int, default=5)
	p.add_argument("--seed", type=int, default=7)
	p.add_argument("--per-dimension", action="store_true", default=True)
	p.add_argument("--no-per-dimension", dest="per_dimension", action="store_false")
	p.add_argument("--l2-to-uniform", type=float, default=0.0)
	p.add_argument("--allow-negative-a", action="store_true")
	args = p.parse_args()

	root = Path.cwd()
	human_dir = root / "images" / "human"
	analysis_dir = root / "images" / "analysis"

	# Prepare output dirs
	out_baseline = human_dir / "weights_baseline"
	out_calib = human_dir / "weights_calibrated"
	out_cv = human_dir / "weights_cv"
	out_baseline.mkdir(parents=True, exist_ok=True)
	out_calib.mkdir(parents=True, exist_ok=True)
	out_cv.mkdir(parents=True, exist_ok=True)

	# 1) Produce baseline outputs into its folder
	human_b = baseline.load_human_scores(human_dir)
	llm_b = baseline.load_llm_scores(analysis_dir)
	merged_b = baseline.build_training_table(human_b, llm_b)
	weights_b = baseline.compute_weights(merged_b, per_dimension=args.per_dimension)
	fitted_b = baseline.apply_weights(merged_b, weights_b)
	weights_b.to_csv(out_baseline / ("llm_weights_by_dimension.csv" if args.per_dimension else "llm_weights.csv"), index=False)
	fitted_b.to_csv(out_baseline / "llm_weighted_fit.csv", index=False)
	mse_b_train = _mse(fitted_b["score"].to_numpy(), fitted_b["pred_score"].to_numpy())

	# 2) Produce calibrated outputs into its folder
	result_csv = human_dir / "result.csv"
	map_csv = human_dir / "map.csv"
	analysis_csv = analysis_dir / "analysis_summary_3d.csv"
	human_c = calibrated.load_human_scores(result_csv, map_csv)
	llm_c = calibrated.load_llm_scores(analysis_csv, group_norm_cols=["judge", "dimension"])
	merged_c = calibrated.build_training_table(human_c, llm_c)

	# Use the calibrated script's own fitting routine (with all-rows a,b refit inside that script).
	# Here we call its CLI-equivalent behavior by directly invoking its main pieces.
	# We'll fit per-dimension weights and then apply on all rows with per-dimension (a,b) refit.
	judge_cols_c = [c for c in merged_c.columns if c not in {"dimension", "generator", "method", "score"}]
	weight_rows: list[pd.DataFrame] = []
	pred_rows: list[pd.DataFrame] = []
	for dim, sub in (merged_c.groupby("dimension") if args.per_dimension else [("all", merged_c)]):
		X = sub[judge_cols_c].to_numpy(dtype=float)
		X = _impute_col_mean(X)
		y = sub["score"].to_numpy(dtype=float)
		w, a_train, b_train = calibrated.fit_weights_one(
			X,
			y,
			calibrate=True,
			a_nonneg=(not args.allow_negative_a),
			l2_to_uniform=args.l2_to_uniform,
			rng=np.random.default_rng(args.seed),
		)
		z = X @ w
		a_all, b_all = calibrated._fit_affine(z, y, a_nonneg=(not args.allow_negative_a))
		pred = a_all * z + b_all

		w_df = pd.DataFrame({"judge": judge_cols_c, "weight": w})
		w_df.insert(0, "dimension", dim)
		w_df["a"] = float(a_all)
		w_df["b"] = float(b_all)
		w_df["a_train"] = float(a_train)
		w_df["b_train"] = float(b_train)
		w_df["all_mse"] = _mse(y, pred)
		weight_rows.append(w_df)

		p_df = sub[["dimension", "generator", "method", "score"]].copy()
		p_df["pred_score"] = pred
		pred_rows.append(p_df)

	weights_c = pd.concat(weight_rows, ignore_index=True)
	fitted_c = pd.concat(pred_rows, ignore_index=True)
	weights_c.to_csv(
		out_calib / ("llm_weights_calibrated_by_dimension.csv" if args.per_dimension else "llm_weights_calibrated.csv"),
		index=False,
	)
	fitted_c.to_csv(out_calib / "llm_weighted_fit_calibrated.csv", index=False)
	mse_c_train = _mse(fitted_c["score"].to_numpy(), fitted_c["pred_score"].to_numpy())

	# 3) Cross-validation predictions (out-of-fold)
	pred_b = cv_predict_baseline(merged_b, per_dimension=args.per_dimension, cv=args.cv, k=args.k, seed=args.seed)
	pred_c = cv_predict_calibrated(
		merged_c,
		per_dimension=args.per_dimension,
		cv=args.cv,
		k=args.k,
		seed=args.seed,
		l2_to_uniform=args.l2_to_uniform,
		a_nonneg=(not args.allow_negative_a),
	)
	pred_all = pd.concat([pred_b, pred_c], ignore_index=True)
	pred_all.to_csv(out_cv / "cv_predictions.csv", index=False)

	summary = _summarize(pred_all)
	summary["cv"] = args.cv
	summary["k"] = int(args.k) if args.cv == "kfold" else 0
	summary["seed"] = int(args.seed)

	# Add train MSE for context
	summary["train_mse"] = np.nan
	summary.loc[summary["model"] == "baseline", "train_mse"] = float(mse_b_train)
	summary.loc[summary["model"] == "calibrated", "train_mse"] = float(mse_c_train)

	summary.to_csv(out_cv / "cv_summary.csv", index=False)

	print("Baseline outputs:", out_baseline)
	print("Calibrated outputs:", out_calib)
	print("CV outputs:", out_cv)
	print("Train MSE baseline:", float(mse_b_train))
	print("Train MSE calibrated:", float(mse_c_train))
	print("CV summary written to:", out_cv / "cv_summary.csv")


if __name__ == "__main__":
	main()
