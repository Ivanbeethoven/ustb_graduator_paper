#!/usr/bin/env python
# -*- coding: utf-8 -*-

    # Some exports have an empty column header for the CWE column.
    for name in fieldnames:
            continue
            return name

    # Heuristics: a header containing 'CWE'
    for name in fieldnames:
        if name and "CWE" in str(name).upper():
            return name

    # Fallback to last column
    return fieldnames[-1]


def _extract_cwe_ids(text: str) -> list[str]:
    if not text:
        return []
    # accept tokens separated by comma/semicolon/pipe/newline
    return sorted(set(CWE_ID_RE.findall(text)))


def _extract_cwe_name_map(class_rows: list[dict]) -> dict[str, str]:
    # Build a map like CWE-269 -> Improper Privilege Management (or Chinese if present)
    if not class_rows:
        return {}

    fieldnames = list(class_rows[0].keys())
    cwe_col = _pick_cwe_column(fieldnames)

    name_map: dict[str, str] = {}

    for r in class_rows:
        raw = (r.get(cwe_col) or "").strip()
        if not raw:
            continue

        # Common patterns:
        # - "CWE-269: Improper Privilege Management, CWE-863: Incorrect Authorization"
        # - "CWE-269, CWE-863" (no names)
        # We'll parse "CWE-xxx: name" when present.
        for token in re.split(r"[;,\n\r|]+", raw):
            token = token.strip()
            if not token:
                continue
            m = CWE_ID_RE.search(token)
            if not m:
                continue
            cwe_id = m.group(0)
            if ":" in token:
                # take the part after ':' as the name
                name = token.split(":", 1)[1].strip()
                if name:
                    name_map.setdefault(cwe_id, name)

    return name_map


def _escape_latex(s: str) -> str:
    # Minimal escaping for LaTeX text fields
    if s is None:
        return ""
    s = str(s)
    s = s.replace("\\", r"\textbackslash{}");
    s = s.replace("&", r"\&")
    s = s.replace("%", r"\%")
    s = s.replace("$", r"\$")
    s = s.replace("#", r"\#")
    s = s.replace("_", r"\_")
    s = s.replace("{", r"\{")
    s = s.replace("}", r"\}")
    s = s.replace("~", r"\textasciitilde{}")
    s = s.replace("^", r"\textasciicircum{}")
    return s


def main():
    root = Path(__file__).resolve().parent

    class_csv = root / "分类漏洞.csv"
    raw_csv = root / "raw_results.csv"
    level1_summary_csv = root / "cwe_mapping_summary_level1.csv"

    if not class_csv.exists():
        raise SystemExit(f"Missing file: {class_csv}")
    if not raw_csv.exists():
        raise SystemExit(f"Missing file: {raw_csv}")

    class_rows = _try_read_csv(class_csv)
    raw_rows = _try_read_csv(raw_csv)

    # Determine column names
    class_fieldnames = list(class_rows[0].keys()) if class_rows else []
    raw_fieldnames = list(raw_rows[0].keys()) if raw_rows else []

    class_cwe_col = _pick_cwe_column(class_fieldnames)

    # Build CVE -> classification + cwe tags
    cve_to_class: dict[str, dict] = {}
    for r in class_rows:
        cve = (r.get("CVEID") or "").strip()
        if not cve:
            continue
        cve_to_class[cve] = r

    # Build CWE name map
    cwe_name_map = _extract_cwe_name_map(class_rows)

    # Select top CWEs (full output)
    top_cwes: list[str] = []
    if level1_summary_csv.exists():
        # Read summary and take top by total count across level1
        sum_rows = _try_read_csv(level1_summary_csv)
        c = Counter()
        for r in sum_rows:
            cwe = (r.get("CWE") or "").strip()
            if not cwe:
                continue
            try:
                cnt = int(float(r.get("count") or 0))
            except Exception:
                cnt = 0
            c[cwe] += cnt
        top_cwes = [k for k, _ in c.most_common(6)]
    else:
        # Fallback: compute from 分类漏洞.csv
        c = Counter()
        for r in class_rows:
            cwe_raw = (r.get(class_cwe_col) or "")
            for cwe_id in _extract_cwe_ids(cwe_raw):
                c[cwe_id] += 1
        top_cwes = [k for k, _ in c.most_common(6)]

    # A thesis-friendly brief selection (3–4 items, stable order)
    brief_cwes = ["CWE-863", "CWE-269", "CWE-22", "CWE-287"]

    # Prefer a few well-known CVEs (if present) so the examples are stable and recognizable.
    preferred_cves_by_cwe: dict[str, list[str]] = {
        "CWE-863": ["CVE-2019-11247"],
        "CWE-269": ["CVE-2022-29179", "CVE-2021-43858"],
        "CWE-22": ["CVE-2022-24730", "CVE-2022-24877"],
        "CWE-287": ["CVE-2022-29165", "CVE-2022-23652"],
    }

    # Short Chinese gloss for a few CWEs (to make the paper explanation more readable)
    cwe_zh_gloss: dict[str, str] = {
        "CWE-863": "授权不当",
        "CWE-269": "权限/访问控制管理不当",
        "CWE-22": "路径遍历",
        "CWE-287": "认证不当",
    }

    # Build CWE -> examples (try to align with raw_results summary)
    examples_by_cwe: dict[str, list[CveExample]] = defaultdict(list)

    for rr in raw_rows:
        cve = (rr.get("CVEID") or rr.get("CVE") or "").strip()
        if not cve:
            continue
        if cve not in cve_to_class:
            continue

        cr = cve_to_class[cve]
        cwe_raw = (cr.get(class_cwe_col) or "")
        cwe_ids = _extract_cwe_ids(cwe_raw)
        if not cwe_ids:
            continue

        app = (rr.get("Third-party Applications") or rr.get("Third Party Applications") or "").strip()
        summary = (rr.get("Summary") or "").strip().replace("\n", " ")
        if not summary:
            continue

        level1 = (cr.get("成因一级分类") or "").strip()
        level2 = (cr.get("成因二级分类") or "").strip()

        ex = CveExample(
            cve=cve,
            app=app,
            summary=summary,
            level1=level1,
            level2=level2,
            cwe_ids=cwe_ids,
        )

        for cid in cwe_ids:
            if cid in top_cwes or cid in brief_cwes:
                examples_by_cwe[cid].append(ex)

    # Keep 2 examples per CWE (full), de-dup by CVE
    picked: dict[str, list[CveExample]] = {}
    for cid in top_cwes:
        seen = set()
        out = []
        for ex in examples_by_cwe.get(cid, []):
            if ex.cve in seen:
                continue
            seen.add(ex.cve)
            out.append(ex)
            if len(out) >= 2:
                break
        picked[cid] = out

    # Keep 1 example per CWE (brief), with preferred CVEs if available
    picked_brief: dict[str, list[CveExample]] = {}
    for cid in brief_cwes:
        pool = examples_by_cwe.get(cid, [])
        pref = preferred_cves_by_cwe.get(cid, [])
        chosen: list[CveExample] = []
        seen = set()

        # preferred first
        for cve in pref:
            for ex in pool:
                if ex.cve == cve and ex.cve not in seen:
                    chosen.append(ex)
                    seen.add(ex.cve)
                    break
            if chosen:
                break

        # fallback
        if not chosen:
            for ex in pool:
                if ex.cve in seen:
                    continue
                chosen.append(ex)
                break

        picked_brief[cid] = chosen

    out_dir = root / "outputs"
    out_dir.mkdir(exist_ok=True)

    # Markdown output (full)
    md_path = out_dir / "cwe_cve_examples.md"
    with md_path.open("w", encoding="utf-8", newline="") as f:
        f.write("# CWE 名称解释与 CVE 示例（自动抽取）\n\n")
        f.write("说明：从 `分类漏洞.csv` 的 CWE 标签与 `raw_results.csv` 的摘要字段抽取。\n\n")
        for cid in top_cwes:
            name = cwe_name_map.get(cid, "(未提供名称)")
            f.write(f"## {cid} — {name}\n\n")
            if not picked.get(cid):
                f.write("未在 raw_results.csv 中匹配到可用摘要的 CVE 示例。\n\n")
                continue
            f.write("| CVE | 组件/软件 | 成因(一级/二级) | 摘要(截断) |\n")
            f.write("|---|---|---|---|\n")
            for ex in picked[cid]:
                summ = ex.summary
                if len(summ) > 160:
                    summ = summ[:160] + "…"
                f.write(
                    "| "
                    + " | ".join(
                        [
                            ex.cve,
                            ex.app or "-",
                            f"{ex.level1}/{ex.level2}" if (ex.level1 or ex.level2) else "-",
                            summ.replace("|", "\\|"),
                        ]
                    )
                    + " |\n"
                )
            f.write("\n")

    # Markdown output (brief)
    md_brief_path = out_dir / "cwe_cve_examples_brief.md"
    with md_brief_path.open("w", encoding="utf-8", newline="") as f:
        f.write("# 关键 CWE 与 CVE 示例（精简版）\n\n")
        f.write("说明：选取 4 个与权限提升分析最相关且高频的 CWE，并为每个 CWE 给出 1 个样本内代表性 CVE。\n\n")
        for cid in brief_cwes:
            name = cwe_name_map.get(cid, "")
            zh = cwe_zh_gloss.get(cid, "")
            title = cid
            if name:
                title += f" — {name}"
            if zh:
                title += f"（{zh}）"
            f.write(f"## {title}\n\n")
            ex_list = picked_brief.get(cid, [])
            if not ex_list:
                f.write("未在 raw_results.csv 中匹配到可用摘要的 CVE 示例。\n\n")
                continue
            ex = ex_list[0]
            summ = ex.summary
            if len(summ) > 240:
                summ = summ[:240] + "…"
            f.write(f"- CVE：{ex.cve}\n")
            if ex.app:
                f.write(f"- 组件/软件：{ex.app}\n")
            if ex.level1 or ex.level2:
                f.write(f"- 成因映射：{ex.level1}/{ex.level2}\n")
            f.write(f"- 摘要：{summ}\n\n")

    # LaTeX snippet output (full)
    tex_path = out_dir / "cwe_cve_examples.tex"
    with tex_path.open("w", encoding="utf-8", newline="") as f:
        f.write("% Auto-generated by extract_cwe_cve_examples.py\n")
        f.write("% Copy/paste into chap3.tex where appropriate.\n\n")
        for cid in top_cwes:
            name = cwe_name_map.get(cid, "")
            title = f"{cid}"
            if name:
                title += f"（{name}）"
            f.write(r"\paragraph{" + _escape_latex(title) + r"}" + "\n")
            if not picked.get(cid):
                f.write("未能在样本中匹配到可用的 CVE 摘要示例。\n\n")
                continue
            # 1-2 short examples as inline text
            for ex in picked[cid]:
                summ = ex.summary.strip()
                if len(summ) > 220:
                    summ = summ[:220] + "..."
                f.write(
                    r"\noindent\textbf{" + _escape_latex(ex.cve) + r"}"
                    + (r"（" + _escape_latex(ex.app) + r"）" if ex.app else "")
                    + r"："
                    + _escape_latex(summ)
                )
                if ex.level1 or ex.level2:
                    f.write(
                        r"（成因：" + _escape_latex(ex.level1) + r"/" + _escape_latex(ex.level2) + r"）"
                    )
                f.write("\\\n")
            f.write("\n")

    # LaTeX snippet output (brief)
    tex_brief_path = out_dir / "cwe_cve_examples_brief.tex"
    with tex_brief_path.open("w", encoding="utf-8", newline="") as f:
        f.write("% Auto-generated by extract_cwe_cve_examples.py\n")
        f.write("% Brief version for thesis writing.\n\n")
        for cid in brief_cwes:
            name = cwe_name_map.get(cid, "")
            zh = cwe_zh_gloss.get(cid, "")
            title = cid
            if name:
                title += f": {name}"
            if zh:
                title += f"（{zh}）"

            # One-sentence definition (kept short; avoids over-claiming)
            if cid == "CWE-863":
                defin = "授权逻辑存在错误或缺失，导致未授权主体获得本应受限的资源访问。"
            elif cid == "CWE-269":
                defin = "权限管理或访问控制配置不当，使得主体获得超过最小权限原则的能力。"
            elif cid == "CWE-22":
                defin = "对路径/目录边界限制不足，攻击者可利用相对路径等手段访问受限目录之外的文件。"
            elif cid == "CWE-287":
                defin = "认证流程不完善（例如绕过、校验缺失或错误），导致身份校验被规避。"
            else:
                defin = ""

            f.write(r"\paragraph{" + _escape_latex(title) + r"}" + "\n")
            if defin:
                f.write(_escape_latex(defin) + "\\\n")

            ex_list = picked_brief.get(cid, [])
            if not ex_list:
                f.write("未能在样本中匹配到可用的 CVE 摘要示例。\n\n")
                continue
            ex = ex_list[0]
            summ = ex.summary.strip()
            if len(summ) > 260:
                summ = summ[:260] + "..."

            f.write(
                r"\noindent\textbf{" + _escape_latex(ex.cve) + r"}"
                + (r"（" + _escape_latex(ex.app) + r"）" if ex.app else "")
                + r"："
                + _escape_latex(summ)
            )
            if ex.level1 or ex.level2:
                f.write(r"（成因映射：" + _escape_latex(ex.level1) + r"/" + _escape_latex(ex.level2) + r"）")
            f.write("\\\n\n")

    print("OK")
    print(f"- Markdown: {md_path}")
    print(f"- LaTeX:    {tex_path}")
    print(f"- Markdown (brief): {md_brief_path}")
    print(f"- LaTeX (brief):    {tex_brief_path}")
    print("\nTop CWEs:")
    for cid in top_cwes:
        nm = cwe_name_map.get(cid, "(未提供名称)")
        print(f"  {cid} - {nm}")


if __name__ == "__main__":
    main()
