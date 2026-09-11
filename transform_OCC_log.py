#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
解析 step_merge_tool.py 產生的 log，統計三階段合併
（精確 / 微擾動 / 模糊）的觸發比例、成功修復數與階段成功率。

用法:
    python parse_merge_log.py <log_file>
    python parse_merge_log.py <log_file> --csv merge_stats.csv

統計定義:
    - 每個零件進入 stubborn_fuse 後，會「終結」在某一階段（精確/微擾動/模糊）。
    - 觸發比例   = 終結於該階段的零件數 / 全部嘗試合併的零件數
    - 成功修復數 = 該階段促成的「true merge successful」次數
    - 階段成功率 = 成功修復數 / 終結於該階段的零件數
"""

import sys
import argparse
import csv

# 對應 stubborn_fuse 各階段在 log 中的特徵字串
MARK_EXACT  = "merged perfectly (Exact Match)"        # 階段1 精確合併 成功
MARK_NUDGE  = "merged via Micro-Nudge"                # 階段2 微擾動合併 成功
MARK_FUZZY  = "merged via Fuzzy("                     # 階段3 模糊合併 成功(單一實體)
MARK_WARN   = "Kept anyway"                           # 階段3 模糊合併 但多實體(假合併候選)
MARK_FAILED = "could not be forced into the solid"    # 三階段全敗
MARK_TRUE   = "true merge successful"                 # smart_fuse 認定為真正成功修復


def parse(path):
    c = {
        "exact_ok": 0, "nudge_ok": 0, "fuzzy_ok": 0,
        "warn_kept": 0, "failed": 0,
        "true_exact": 0, "true_nudge": 0, "true_fuzzy": 0,
        "true_total": 0, "true_unknown": 0,
    }
    last_stage = None  # 最近一次 stubborn 階段性成功屬於哪一階段

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if MARK_EXACT in line:
                c["exact_ok"] += 1
                last_stage = "exact"
            elif MARK_NUDGE in line:
                c["nudge_ok"] += 1
                last_stage = "nudge"
            elif MARK_FUZZY in line:
                c["fuzzy_ok"] += 1
                last_stage = "fuzzy"
            elif MARK_WARN in line:
                c["warn_kept"] += 1
                last_stage = None      # 假合併候選，等 Diagnosis 判定，本身不計階段成功
            elif MARK_FAILED in line:
                c["failed"] += 1
                last_stage = None
            elif MARK_TRUE in line:
                c["true_total"] += 1
                if last_stage == "exact":
                    c["true_exact"] += 1
                elif last_stage == "nudge":
                    c["true_nudge"] += 1
                elif last_stage == "fuzzy":
                    c["true_fuzzy"] += 1
                else:
                    c["true_unknown"] += 1
                last_stage = None
    return c


def pct(num, den):
    return (num / den * 100.0) if den else 0.0


def build_rows(c):
    total = c["exact_ok"] + c["nudge_ok"] + c["fuzzy_ok"] + c["warn_kept"] + c["failed"]
    # 各階段「終結」零件數
    term_exact = c["exact_ok"]
    term_nudge = c["nudge_ok"]
    term_fuzzy = c["fuzzy_ok"] + c["warn_kept"] + c["failed"]

    rows = [
        ("精確合併",  term_exact, c["true_exact"]),
        ("微擾動合併", term_nudge, c["true_nudge"]),
        ("模糊合併",  term_fuzzy, c["true_fuzzy"]),
    ]

    out = []
    for name, term, repaired in rows:
        out.append({
            "stage": name,
            "trigger_pct": pct(term, total),
            "repaired": repaired,
            "stage_success_pct": pct(repaired, term),
        })
    out.append({
        "stage": "整體",
        "trigger_pct": 100.0,
        "repaired": c["true_total"],
        "stage_success_pct": pct(c["true_total"], total),
    })
    return out, total


def print_table(rows, total, c):
    print(f"\n總嘗試合併零件數 (stubborn 呼叫次數): {total}")
    print(f"真正成功修復 (true merge) 總數     : {c['true_total']}")
    if c["true_unknown"]:
        print(f"（注意: 有 {c['true_unknown']} 筆 true merge 無法歸到任何階段，"
              f"通常代表 log 片段不完整）")
    print()
    header = f"{'合併階段':<10}{'觸發比例':>10}{'成功修復數':>10}{'階段成功率':>12}"
    print(header)
    print("-" * len(header))
    for r in rows:
        rep = "" if (r["stage"] == "模糊合併" and r["repaired"] == 0) else str(r["repaired"])
        print(f"{r['stage']:<10}{r['trigger_pct']:>9.1f}%"
              f"{rep:>10}{r['stage_success_pct']:>11.1f}%")
    print()
    print("原始計數:")
    print(f"  精確 OK={c['exact_ok']}  微擾動 OK={c['nudge_ok']}  "
          f"模糊 OK(單實體)={c['fuzzy_ok']}  模糊多實體(Kept anyway)={c['warn_kept']}  "
          f"全敗={c['failed']}")


def write_csv(rows, path):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["合併階段", "觸發比例", "成功修復數", "階段成功率"])
        for r in rows:
            rep = "" if (r["stage"] == "模糊合併" and r["repaired"] == 0) else r["repaired"]
            w.writerow([r["stage"], f"{r['trigger_pct']:.1f}%", rep,
                        f"{r['stage_success_pct']:.1f}%"])
    print(f"已輸出 CSV: {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("log", help="log 檔路徑")
    ap.add_argument("--csv", help="另存表格為 CSV", default=None)
    args = ap.parse_args()

    c = parse(args.log)
    rows, total = build_rows(c)
    print_table(rows, total, c)
    if args.csv:
        write_csv(rows, args.csv)


if __name__ == "__main__":
    main()