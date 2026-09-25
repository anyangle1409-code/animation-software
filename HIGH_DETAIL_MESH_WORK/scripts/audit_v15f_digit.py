"""Incremental V15f per-digit gate for ring/pinky local reconstruction.

Usage:
  python scripts/audit_v15f_digit.py ring_L
  python scripts/audit_v15f_digit.py ring_R
  python scripts/audit_v15f_digit.py pinky_L
  python scripts/audit_v15f_digit.py pinky_R

Runs the full general V15 Blender invariant audit, then requires the selected
digit to be no worse than V13e at >35°, >50° and >100° fold measures. Total
>100° digit folds must also not exceed V13e.
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

ROOT = Path(__file__).resolve().parents[1]
VERSION = "v15f_deep_hand_rebuild"
BLEND = ROOT / f"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{VERSION}.blend"
AUDIT = ROOT / "reports" / f"audit_{VERSION}_blender.json"
ORDER = ("ring_L", "ring_R", "pinky_L", "pinky_R")
ALLOWED = set(ORDER)
RING_VISUAL = ROOT / "reports" / "v15f_ring_visual_decision.json"

def find_blender():
    explicit = os.environ.get("BLENDER_EXE")
    if explicit and Path(explicit).is_file():
        return explicit
    found = shutil.which("blender")
    if found:
        return found
    if os.name == "nt":
        hits = sorted(
            glob.glob(r"C:\Program Files\Blender Foundation\Blender *\blender.exe"),
            reverse=True,
        )
        if hits:
            return hits[0]
    raise SystemExit("Blender not found. Set BLENDER_EXE or add Blender to PATH.")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("digit", choices=sorted(ALLOWED))
    args = ap.parse_args()
    digit = args.digit

    if not BLEND.is_file():
        raise SystemExit(f"Missing V15f Blend: {BLEND}")

    exe = find_blender()
    subprocess.run([
        exe, "--background", "--factory-startup",
        "--python", ROOT / "scripts" / "audit_v15_hand_blender.py",
        "--", str(BLEND),
    ], cwd=ROOT, check=True)

    report = json.loads(AUDIT.read_text(encoding="utf-8"))
    baseline = report["baseline_topology"]
    candidate = report["candidate_topology"]
    b = baseline["per_digit_surface"][digit]
    c = candidate["per_digit_surface"][digit]

    movement = report.get("per_digit_original_movement_vs_v13e", {})
    current_surface = candidate["per_digit_surface"]
    allowed_now = set(ORDER[: ORDER.index(digit) + 1])
    frozen_failures = []

    # ring_L has an explicit visual proof and must stay exact while later
    # Stage-A digits are edited.
    if digit != "ring_L":
        if not RING_VISUAL.is_file():
            frozen_failures.append("ring_L visual PASS marker is missing.")
        else:
            visual = json.loads(RING_VISUAL.read_text(encoding="utf-8"))
            expected = visual.get("surface_fingerprint_sha256")
            actual = current_surface.get("ring_L", {}).get("surface_fingerprint_sha256")
            if visual.get("pass") is not True or not expected or expected != actual:
                frozen_failures.append("ring_L approved visual surface changed or is not PASS.")

    # Every previously completed Stage-A digit is frozen by its own numeric gate
    # fingerprint before work may advance to the next digit.
    for previous in ORDER[1:ORDER.index(digit)]:
        gate_path = ROOT / "reports" / f"v15f_{previous}_incremental_gate.json"
        if not gate_path.is_file():
            frozen_failures.append(f"{previous} prior gate is missing.")
            continue
        prior = json.loads(gate_path.read_text(encoding="utf-8"))
        expected = prior.get("candidate", {}).get("surface_fingerprint_sha256")
        actual = current_surface.get(previous, {}).get("surface_fingerprint_sha256")
        if prior.get("pass") is not True or not expected or expected != actual:
            frozen_failures.append(f"{previous} previously passed surface changed.")
    outside_allowed = {
        key: item for key, item in movement.items() if key not in allowed_now
    }

    checks = {
        "general_invariants_pass": bool(report.get("pass")),
        "previous_stage_a_surfaces_frozen": not frozen_failures,
        "only_approved_sequence_digits_changed": all(
            float(item.get("max_move_mm", 0.0)) <= 1e-6
            for item in outside_allowed.values()
        ),
        "total_gt100_folds_not_worse": (
            int(candidate["digit_folds_over_100deg"])
            <= int(baseline["digit_folds_over_100deg"])
        ),
        "digit_gt35_not_worse": (
            float(c["sharp_length_ratio_gt_35"])
            <= float(b["sharp_length_ratio_gt_35"]) + 1e-12
        ),
        "digit_gt50_not_worse": (
            float(c["sharp_length_ratio_gt_50"])
            <= float(b["sharp_length_ratio_gt_50"]) + 1e-12
        ),
        "digit_gt100_folds_not_worse": (
            int(c["dihedral_edge_count_gt_deg"]["100"])
            <= int(b["dihedral_edge_count_gt_deg"]["100"])
        ),
    }

    result = {
        "version": VERSION,
        "digit": digit,
        "baseline": {
            "total_gt100_folds": int(baseline["digit_folds_over_100deg"]),
            "gt35": float(b["sharp_length_ratio_gt_35"]),
            "gt50": float(b["sharp_length_ratio_gt_50"]),
            "gt100_folds": int(b["dihedral_edge_count_gt_deg"]["100"]),
        },
        "candidate": {
            "total_gt100_folds": int(candidate["digit_folds_over_100deg"]),
            "gt35": float(c["sharp_length_ratio_gt_35"]),
            "gt50": float(c["sharp_length_ratio_gt_50"]),
            "gt100_folds": int(c["dihedral_edge_count_gt_deg"]["100"]),
            "surface_fingerprint_sha256": c.get("surface_fingerprint_sha256"),
        },
        "approved_changed_digits": sorted(allowed_now),
        "frozen_surface_failures": frozen_failures,
        "scope_movement": movement,
        "checks": checks,
        "pass": all(checks.values()),
        "next_if_pass": (
            "Save a checkpoint and continue only to the next planned ring/pinky digit."
        ),
        "next_if_fail": (
            "Do not propagate this topology strategy. Keep edits local to the current digit."
        ),
    }

    out = ROOT / "reports" / f"v15f_{digit}_incremental_gate.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    subprocess.run([
        sys.executable, ROOT / "scripts" / "write_v15f_handoff.py",
    ], cwd=ROOT, check=False)
    if not result["pass"]:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
