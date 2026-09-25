"""Incremental V15f Stage-B gate for index/middle.

Usage:
  python scripts/audit_v15f_stage_b_digit.py index_L
  python scripts/audit_v15f_stage_b_digit.py index_R
  python scripts/audit_v15f_stage_b_digit.py middle_L
  python scripts/audit_v15f_stage_b_digit.py middle_R

Requires Stage-A visual PASS and freezes the approved ring/pinky fingerprints.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VERSION="v15f_deep_hand_rebuild"
BLEND=ROOT/f"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{VERSION}.blend"
AUDIT=ROOT/"reports"/f"audit_{VERSION}_blender.json"
STAGE_A_VISUAL=ROOT/"reports"/"v15f_stage_a_visual_decision.json"
ORDER=("index_L","index_R","middle_L","middle_R")
STAGE_A_DIGITS=("ring_L","ring_R","pinky_L","pinky_R")

def find_blender():
    explicit=os.environ.get("BLENDER_EXE")
    if explicit and Path(explicit).is_file():
        return explicit
    found=shutil.which("blender")
    if found:
        return found
    if os.name=="nt":
        hits=sorted(glob.glob(r"C:\Program Files\Blender Foundation\Blender *\blender.exe"),reverse=True)
        if hits:
            return hits[0]
    raise SystemExit("Blender not found. Set BLENDER_EXE or add Blender to PATH.")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("digit",choices=ORDER)
    args=ap.parse_args()
    digit=args.digit

    if not BLEND.is_file():
        raise SystemExit(f"Missing V15f Blend: {BLEND}")
    if not STAGE_A_VISUAL.is_file():
        raise SystemExit("Missing Stage-A visual decision. Finish Stage A before Stage B.")
    stage=json.loads(STAGE_A_VISUAL.read_text(encoding="utf-8"))
    if stage.get("pass") is not True:
        raise SystemExit("Stage-A visual decision is not PASS.")
    approved=stage.get("surface_fingerprints_sha256") or {}
    if any(not approved.get(key) for key in STAGE_A_DIGITS):
        raise SystemExit("Stage-A visual decision lacks approved ring/pinky fingerprints.")

    exe=find_blender()
    subprocess.run([
        exe,"--background","--factory-startup",
        "--python",ROOT/"scripts"/"audit_v15_hand_blender.py",
        "--",str(BLEND),
    ],cwd=ROOT,check=True)

    report=json.loads(AUDIT.read_text(encoding="utf-8"))
    baseline=report["baseline_topology"]
    candidate=report["candidate_topology"]
    current=candidate["per_digit_surface"]
    movement=report.get("per_digit_original_movement_vs_v13e",{})

    failures=[]
    if not report.get("pass"):
        failures.append("General V15 invariant audit failed.")

    for key in STAGE_A_DIGITS:
        actual=current.get(key,{}).get("surface_fingerprint_sha256")
        if actual != approved.get(key):
            failures.append(f"{key}: approved Stage-A surface fingerprint changed.")

    allowed=set(STAGE_A_DIGITS)|set(ORDER[:ORDER.index(digit)+1])
    for key,item in movement.items():
        if key not in allowed and float(item.get("max_move_mm",0.0))>1e-6:
            failures.append(
                f"{key}: moved before its Stage-B turn ({item.get('max_move_mm')} mm)."
            )

    b=baseline["per_digit_surface"][digit]
    c=current[digit]
    b35=float(b["sharp_length_ratio_gt_35"])
    c35=float(c["sharp_length_ratio_gt_35"])
    b50=float(b["sharp_length_ratio_gt_50"])
    c50=float(c["sharp_length_ratio_gt_50"])
    b100=int(b["dihedral_edge_count_gt_deg"]["100"])
    c100=int(c["dihedral_edge_count_gt_deg"]["100"])

    if c35>b35+1e-12:
        failures.append(f"{digit}: >35deg sharp ratio worsened {b35:.10f} -> {c35:.10f}")
    if c50>b50+1e-12:
        failures.append(f"{digit}: >50deg sharp ratio worsened {b50:.10f} -> {c50:.10f}")
    if c100>b100:
        failures.append(f"{digit}: >100deg fold count worsened {b100} -> {c100}")

    bt=int(baseline["digit_folds_over_100deg"])
    ct=int(candidate["digit_folds_over_100deg"])
    if ct>bt:
        failures.append(f"Total >100deg digit folds worsened {bt} -> {ct}.")

    result={
        "version":VERSION,
        "stage":"B",
        "digit":digit,
        "approved_stage_a_fingerprints":approved,
        "approved_changed_digits":sorted(allowed),
        "baseline":{
            "gt35":b35,"gt50":b50,"gt100_folds":b100,
            "total_gt100_folds":bt,
        },
        "candidate":{
            "gt35":c35,"gt50":c50,"gt100_folds":c100,
            "total_gt100_folds":ct,
            "surface_fingerprint_sha256":c.get("surface_fingerprint_sha256"),
        },
        "scope_movement":movement,
        "pass":not failures,
        "failures":failures,
        "next_if_pass":"Generate and inspect the matched per-digit visual proof before continuing.",
        "next_if_fail":"Keep edits local to the current digit and do not propagate the strategy.",
    }
    out=ROOT/"reports"/f"v15f_stage_b_{digit}_gate.json"
    out.write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))
    subprocess.run([sys.executable,ROOT/"scripts"/"write_v15f_handoff.py"],cwd=ROOT,check=False)
    if failures:
        raise SystemExit(1)

if __name__=="__main__":
    main()
