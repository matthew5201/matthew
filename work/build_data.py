# /// script
# requires-python = ">=3.10"
# dependencies = ["pandas"]
# ///
"""
把 data/ 裡的三個 CSV（在學人數、休學人數、系所對照表）整理成網頁可以直接載入的
docs/data.js，只保留網頁會用到的欄位，並先依這些欄位加總，讓檔案小一點。
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "docs" / "data.js"

ENROLL_KEYS = ["semester", "college", "dept", "degree", "gender"]
LEAVE_KEYS = ["semester", "college", "dept", "degree", "gender", "reason"]


def build_enrollment():
    df = pd.read_csv(DATA / "enrollment.csv", encoding="utf-8-sig")
    df = df.groupby(ENROLL_KEYS, as_index=False)["count"].sum()
    return df


def build_leave():
    df = pd.read_csv(DATA / "leave.csv", encoding="utf-8-sig")
    df = df.groupby(LEAVE_KEYS, as_index=False)[["new_leave", "on_leave_end"]].sum()
    return df


def build_dept_mapping():
    df = pd.read_csv(DATA / "dept_mapping.csv", encoding="utf-8-sig")
    depts = []
    for _, row in df.iterrows():
        aliases_raw = row["aliases"]
        aliases = []
        if isinstance(aliases_raw, str) and aliases_raw.strip():
            aliases = [a.strip() for a in aliases_raw.split(";") if a.strip()]
        depts.append({"dept": row["dept"], "college": row["college"], "aliases": aliases})
    return depts


def main():
    enrollment = build_enrollment()
    leave = build_leave()
    depts = build_dept_mapping()

    enroll_114_1 = int(enrollment.loc[enrollment["semester"] == "114-1", "count"].sum())
    print(f"核對：114-1 在學人數合計 = {enroll_114_1}（應為 10035）")
    assert enroll_114_1 == 10035, "114-1 在學人數合計與預期不符！"

    payload = {
        "semesters": sorted(set(enrollment["semester"]) | set(leave["semester"])),
        "colleges": sorted(set(enrollment["college"]) | set(leave["college"])),
        "degrees": sorted(set(enrollment["degree"]) | set(leave["degree"])),
        "genders": sorted(set(enrollment["gender"]) | set(leave["gender"])),
        "reasons": sorted(set(leave["reason"])),
        "depts": depts,
        "enrollment": enrollment.to_dict(orient="records"),
        "leave": leave.to_dict(orient="records"),
    }

    js = "// 由 work/build_data.py 自動產生，請勿手動編輯\nwindow.BI_DATA = " + json.dumps(
        payload, ensure_ascii=False, separators=(",", ":")
    ) + ";\n"
    OUT.write_text(js, encoding="utf-8")

    size_kb = OUT.stat().st_size / 1024
    print(f"已寫入 {OUT.relative_to(ROOT)}，大小 {size_kb:.1f} KB")
    print(f"enrollment 列數：{len(enrollment)}，leave 列數：{len(leave)}，系所數：{len(depts)}")


if __name__ == "__main__":
    main()
