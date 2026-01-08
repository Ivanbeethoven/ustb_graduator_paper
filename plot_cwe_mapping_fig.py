from __future__ import annotations

import pathlib

import pandas as pd


def _configure_matplotlib() -> None:
    # Import after installing matplotlib
    import matplotlib as mpl

    # Prefer common Chinese fonts on Windows; fallback is OK.
    mpl.rcParams["font.sans-serif"] = [
        "Microsoft YaHei",
        "SimHei",
        "Noto Sans CJK SC",
        "Arial Unicode MS",
        "DejaVu Sans",
    ]
    mpl.rcParams["axes.unicode_minus"] = False


def plot_level1_heatmap(
    csv_path: pathlib.Path,
    out_path: pathlib.Path,
    top_n_cwe: int = 12,
) -> None:
    import matplotlib.pyplot as plt

    df = pd.read_csv(csv_path, encoding="utf-8-sig")

    required_cols = {"成因一级分类", "CWE", "count"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in {csv_path}: {sorted(missing)}")

    # Pick Top-N CWE by overall frequency.
    top_cwes = (
        df.groupby("CWE", as_index=False)["count"].sum().sort_values("count", ascending=False)
    ).head(top_n_cwe)["CWE"].tolist()

    mat = (
        df[df["CWE"].isin(top_cwes)]
        .pivot_table(index="成因一级分类", columns="CWE", values="count", aggfunc="sum", fill_value=0)
    )

    # Stable ordering: rows by total desc, cols by overall desc.
    mat = mat.loc[mat.sum(axis=1).sort_values(ascending=False).index]
    mat = mat[top_cwes]

    fig_w = max(8.5, 0.65 * (len(mat.columns) + 2))
    fig_h = max(3.6, 0.55 * (len(mat.index) + 2))
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=200)

    im = ax.imshow(mat.values, aspect="auto")
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("CVE 样本数（count）")

    ax.set_xticks(range(len(mat.columns)), labels=mat.columns, rotation=45, ha="right")
    ax.set_yticks(range(len(mat.index)), labels=mat.index)

    ax.set_xlabel("CWE（Top-N）")
    ax.set_ylabel("成因一级分类")
    ax.set_title("成因一级分类与 CWE 的对应关系（共现频次）")

    # Annotate counts for readability.
    vmax = mat.values.max() if mat.values.size else 0
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            v = int(mat.iat[i, j])
            if v == 0:
                continue
            ax.text(
                j,
                i,
                str(v),
                ha="center",
                va="center",
                color="white" if vmax and v > 0.55 * vmax else "black",
                fontsize=9,
            )

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)


def main() -> None:
    root = pathlib.Path(__file__).resolve().parent
    csv_level1 = root / "cwe_mapping_summary_level1.csv"
    out_level1 = root / "images" / "cwe_mapping_level1_heatmap.png"

    _configure_matplotlib()
    plot_level1_heatmap(csv_level1, out_level1, top_n_cwe=12)

    print(f"Wrote: {out_level1}")


if __name__ == "__main__":
    main()
