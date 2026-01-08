import csv
import re
from collections import defaultdict
from pathlib import Path


CWE_RE = re.compile(r"CWE-\d+")


def normalize(s: str) -> str:
    return (s or "").strip()


def extract_cwes(raw: str) -> list[str]:
    """Extract CWE ids like 'CWE-862' from a raw string.

    Handles cases like:
    - 'CVE-xxxx,CWE-862,CWE-862: Missing Authorization'
    - '... CWE-862; CWE-269 ...'
    """
    if not raw:
        return []
    cwes = CWE_RE.findall(raw)
    # de-dup while preserving order
    seen = set()
    out: list[str] = []
    for cwe in cwes:
        if cwe not in seen:
            seen.add(cwe)
            out.append(cwe)
    return out


def read_rows(csv_path: Path) -> list[dict[str, str]]:
    # Try UTF-8 with BOM first; fall back to GBK if needed.
    for enc in ("utf-8-sig", "utf-8", "gbk"):
        try:
            with csv_path.open("r", encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            return rows
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("unknown", b"", 0, 1, "Failed to decode CSV with utf-8/gbk")


def main() -> None:
    base = Path(__file__).resolve().parent
    src = base / "分类漏洞.csv"
    if not src.exists():
        raise SystemExit(f"Source CSV not found: {src}")

    rows = read_rows(src)

    # Handle the empty header for the last column (observed in the file).
    # DictReader uses '' as the key for an empty header.
    cwe_col = "" if "" in (rows[0].keys() if rows else []) else None

    # Expected columns
    col_cve = "CVEID"
    col_l1 = "成因一级分类"
    col_l2 = "成因二级分类"
    col_l3 = "成因三级分类"

    # Aggregations
    # level2: (l1, l2, cwe) -> count
    level2_counts: dict[tuple[str, str, str], int] = defaultdict(int)
    level2_samples: dict[tuple[str, str, str], list[str]] = defaultdict(list)

    # level1: (l1, cwe) -> count
    level1_counts: dict[tuple[str, str], int] = defaultdict(int)
    level1_samples: dict[tuple[str, str], list[str]] = defaultdict(list)

    # Track denominators for pct within each category
    denom_l1: dict[str, int] = defaultdict(int)
    denom_l1l2: dict[tuple[str, str], int] = defaultdict(int)

    skipped_no_cwe = 0
    skipped_no_cat = 0

    for r in rows:
        cve = normalize(r.get(col_cve, ""))
        l1 = normalize(r.get(col_l1, ""))
        l2 = normalize(r.get(col_l2, ""))
        l3 = normalize(r.get(col_l3, ""))

        raw_cwe = ""
        if cwe_col is not None:
            raw_cwe = r.get(cwe_col, "") or ""
        else:
            # Try some common names in case the header changes.
            for k in ("CWE", "CWE分类", "CWE/描述", "cwe"):
                if k in r:
                    raw_cwe = r.get(k, "") or ""
                    break

        if not l1 or not l2:
            skipped_no_cat += 1
            continue

        cwes = extract_cwes(raw_cwe)
        if not cwes:
            skipped_no_cwe += 1
            continue

        # Denominator counts are per CVE (not per CWE)
        denom_l1[l1] += 1
        denom_l1l2[(l1, l2)] += 1

        for cwe in cwes:
            key2 = (l1, l2, cwe)
            level2_counts[key2] += 1
            if cve and len(level2_samples[key2]) < 5 and cve not in level2_samples[key2]:
                level2_samples[key2].append(cve)

            key1 = (l1, cwe)
            level1_counts[key1] += 1
            if cve and len(level1_samples[key1]) < 5 and cve not in level1_samples[key1]:
                level1_samples[key1].append(cve)

    out_level2 = base / "cwe_mapping_summary_level2.csv"
    out_level1 = base / "cwe_mapping_summary_level1.csv"

    with out_level2.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "成因一级分类",
            "成因二级分类",
            "CWE",
            "count",
            "pct_within_(一级+二级)",
            "sample_cves",
        ])
        for (l1, l2, cwe), cnt in sorted(level2_counts.items(), key=lambda x: (-x[1], x[0])):
            denom = denom_l1l2.get((l1, l2), 0) or 0
            pct = (cnt / denom) if denom else 0.0
            samples = ";".join(level2_samples[(l1, l2, cwe)])
            w.writerow([l1, l2, cwe, cnt, f"{pct:.4f}", samples])

    with out_level1.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "成因一级分类",
            "CWE",
            "count",
            "pct_within_(一级)",
            "sample_cves",
        ])
        for (l1, cwe), cnt in sorted(level1_counts.items(), key=lambda x: (-x[1], x[0])):
            denom = denom_l1.get(l1, 0) or 0
            pct = (cnt / denom) if denom else 0.0
            samples = ";".join(level1_samples[(l1, cwe)])
            w.writerow([l1, cwe, cnt, f"{pct:.4f}", samples])

    print("Wrote:")
    print(f"- {out_level2}")
    print(f"- {out_level1}")
    print(f"Rows read: {len(rows)}")
    print(f"Skipped (missing category l1/l2): {skipped_no_cat}")
    print(f"Skipped (no CWE extracted): {skipped_no_cwe}")


if __name__ == "__main__":
    main()
