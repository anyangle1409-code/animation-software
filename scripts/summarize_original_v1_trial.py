#!/usr/bin/env python3
"""Summarize an ORIGINAL-v1 experimental candidate against named predecessors.

This is a deterministic trial classifier, not a production-approval tool.
It consumes the existing strict comparator JSON files and never changes gates,
baselines, assets, or approval flags.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RC = ROOT / "ORIGINAL_V1_WORK" / "candidates" / "repair_checks"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("candidate", help="for example r30")
    ap.add_argument("baselines", nargs="+", help="for example r29 r28")
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--markdown-out", type=Path)
    args = ap.parse_args()

    rev = args.candidate
    rows = []
    for base in args.baselines:
        p = RC / ("full_" + rev + "_comparison_vs_" + base + ".json")
        if not p.exists():
            raise SystemExit("missing comparison: " + str(p))
        x = load(p)
        rows.append({
            "baseline": base,
            "status": x["status"],
            "baseline_failed_checks": int(x["baseline_failed_checks"]),
            "candidate_failed_checks": int(x["candidate_failed_checks"]),
            "delta_failed_checks": int(x["delta_failed_checks"]),
            "regression_count": int(x["regression_count"]),
            "improvement_count": int(x["improvement_count"]),
        })

    r2_path = RC / ("full_" + rev + "_comparison_vs_R2.json")
    if not r2_path.exists():
        raise SystemExit("missing R2 comparison: " + str(r2_path))
    r2 = load(r2_path)

    no_predecessor_regressions = all(x["regression_count"] == 0 for x in rows)
    fewer_than_all = all(x["candidate_failed_checks"] < x["baseline_failed_checks"] for x in rows)
    no_more_than_all = all(x["candidate_failed_checks"] <= x["baseline_failed_checks"] for x in rows)

    if no_predecessor_regressions and fewer_than_all:
        classification = "STRICT_IMPROVEMENT_OVER_ALL_PREDECESSORS"
    elif no_predecessor_regressions and no_more_than_all:
        classification = "NON_REGRESSING_NO_WORSE_FAILURE_COUNT"
    else:
        classification = "TRADEOFF_OR_REGRESSION"

    result = {
        "schema_version": 1,
        "candidate": rev,
        "classification": classification,
        "production_approved": False,
        "rule": "Experimental comparison only. Production approval remains a separate gated decision.",
        "comparisons": rows,
        "versus_R2": {
            "status": r2["status"],
            "baseline_failed_checks": int(r2["baseline_failed_checks"]),
            "candidate_failed_checks": int(r2["candidate_failed_checks"]),
            "delta_failed_checks": int(r2["delta_failed_checks"]),
            "regression_count": int(r2["regression_count"]),
            "improvement_count": int(r2["improvement_count"]),
        },
    }

    jout = args.json_out or (RC / ("full_" + rev + "_trial_summary.json"))
    mout = args.markdown_out or (RC / ("full_" + rev + "_trial_summary.md"))
    jout.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# ORIGINAL v1 " + rev + " experimental trial summary",
        "",
        "- Classification: **" + classification + "**",
        "- Production approved: **NO**",
        "- This summary does not change R2, thresholds or any approval flag.",
        "",
        "| Baseline | Comparator | Failed before | Failed candidate | Delta | Regressions | Improvements |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for x in rows:
        lines.append("| {0} | {1} | {2} | {3} | {4:+d} | {5} | {6} |".format(
            x["baseline"], x["status"], x["baseline_failed_checks"],
            x["candidate_failed_checks"], x["delta_failed_checks"],
            x["regression_count"], x["improvement_count"]))
    lines += [
        "",
        "## Versus pinned R2",
        "",
        "- Comparator: **" + r2["status"] + "**",
        "- Failed checks: {0} -> {1} ({2:+d})".format(
            r2["baseline_failed_checks"], r2["candidate_failed_checks"], r2["delta_failed_checks"]),
        "- Strict severity regressions: " + str(r2["regression_count"]),
        "- Material improvements: " + str(r2["improvement_count"]),
        "",
    ]
    mout.write_text("\n".join(lines), encoding="utf-8")
    print("TRIAL SUMMARY", rev, classification)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
