"""Merge the per-group repair-check pose reports of one candidate into a full report.

python scripts/merge_original_v1_repair_group_reports.py <rN> [--prior <rM>]

Reads ORIGINAL_V1_WORK/candidates/repair_checks/{shoulder,hand,hip,pushup,row}_<rN>/
pose_test_report.json (produced by RUN_ORIGINAL_V1_REPAIR_CHECK.bat), writes
full_<rN>_merged_pose_report.json (all R2 poses except the weight-independent
neutral rest pose), then runs the committed evaluator, repair queue and the
comparator against pinned R2 and, optionally, against a prior candidate's merged
report. Read-only with respect to candidates, thresholds and the R2 baseline.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAND = ROOT / "ORIGINAL_V1_WORK" / "candidates"
RC = CAND / "repair_checks"
R2 = CAND / "pose_test_report_r2.json"
GROUPS = ("shoulder", "hand", "hip", "pushup", "row")


def run(args):
    print(">", " ".join(str(a) for a in args), flush=True)
    r = subprocess.run([sys.executable, *map(str, args)], cwd=ROOT, capture_output=True, text=True)
    print(r.stdout[-3000:], r.stderr[-2000:], sep="", flush=True)
    return r.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rev")
    ap.add_argument("--prior")
    a = ap.parse_args()
    base = json.loads(R2.read_text(encoding="utf-8"))
    merged = {}
    for g in GROUPS:
        f = RC / f"{g}_{a.rev}" / "pose_test_report.json"
        if not f.exists():
            raise SystemExit(f"missing {f}")
        for x in json.loads(f.read_text(encoding="utf-8")):
            merged[x["pose"]] = x
    neutral = RC / f"neutral_{a.rev}" / "pose_test_report.json"   # optional rest-pose control run
    if neutral.exists():
        for x in json.loads(neutral.read_text(encoding="utf-8")):
            merged[x["pose"]] = x
    missing = [x["pose"] for x in base if x["pose"] not in merged]
    if missing not in ([], ["neutral"]):
        raise SystemExit(f"unexpected missing poses: {missing}")
    out = RC / f"full_{a.rev}_merged_pose_report.json"
    out.write_text(json.dumps([merged[x["pose"]] for x in base if x["pose"] in merged], indent=2) + "\n",
                   encoding="utf-8")
    poses = ",".join(x["pose"] for x in base if x["pose"] in merged)
    run(["scripts/evaluate_original_v1_deformation_report.py", out, "--grip-report", out,
         "--profile", "development_blocker", "--require-group", "core_five", "--report-only",
         "--markdown-out", RC / f"full_{a.rev}_deformation_acceptance.md"])
    run(["scripts/build_original_v1_repair_queue.py", out, "--profile", "development_blocker",
         "--require-complete-ownership", "--markdown-out", RC / f"full_{a.rev}_repair_queue.md"])
    run(["scripts/compare_original_v1_deformation_reports.py", R2, out, "--baseline-grip-report", R2,
         "--candidate-grip-report", out, "--profile", "development_blocker", "--poses", poses,
         "--json-out", RC / f"full_{a.rev}_comparison_vs_R2.json"])
    if a.prior:
        prior = RC / f"full_{a.prior}_merged_pose_report.json"
        prior_poses = {x["pose"] for x in json.loads(prior.read_text(encoding="utf-8"))}
        common = ",".join(x["pose"] for x in base if x["pose"] in merged and x["pose"] in prior_poses)
        run(["scripts/compare_original_v1_deformation_reports.py", prior, out, "--baseline-grip-report", prior,
             "--candidate-grip-report", out, "--profile", "development_blocker", "--poses", common,
             "--json-out", RC / f"full_{a.rev}_comparison_vs_{a.prior}.json"])


if __name__ == "__main__":
    main()
