"""Fast V15f proof gate after editing only ring_L.

This is intentionally earlier than AUDIT_V15F_STAGE_A.bat. It answers one
question: did the new local topology strategy improve/hold the left ring
without breaking the general invariants?

Do not mirror the approach to the other fingers until this passes.
"""
from __future__ import annotations

import glob
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "v15f_deep_hand_rebuild"
BLEND = ROOT / f"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{VERSION}.blend"
AUDIT = ROOT / "reports" / f"audit_{VERSION}_blender.json"
OUT = ROOT / "reports" / "v15f_ring_l_proof_gate.json"

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
    if not BLEND.is_file():
        raise SystemExit(f"Missing V15f Blend: {BLEND}")

    exe = find_blender()
    subprocess.run([
        exe, "--background", "--factory-startup",
        "--python", ROOT / "scripts" / "audit_v15_hand_blender.py",
        "--", str(BLEND),
    ], cwd=ROOT, check=True)

    report = json.loads(AUDIT.read_text(encoding="utf-8"))
    b = report["baseline_topology"]
    c = report["candidate_topology"]
    bd = b["per_digit_surface"]["ring_L"]
    cd = c["per_digit_surface"]["ring_L"]

    movement = report.get("per_digit_original_movement_vs_v13e", {})
    outside_ring_l = {
        key: item for key, item in movement.items() if key != "ring_L"
    }
    checks = {
        "general_invariants_pass": bool(report.get("pass")),
        "only_ring_L_original_positions_changed": all(
            float(item.get("max_move_mm", 0.0)) <= 1e-6
            for item in outside_ring_l.values()
        ),
        "total_gt100_folds_not_worse": (
            int(c["digit_folds_over_100deg"]) <= int(b["digit_folds_over_100deg"])
        ),
        "ring_L_gt35_not_worse": (
            float(cd["sharp_length_ratio_gt_35"])
            <= float(bd["sharp_length_ratio_gt_35"]) + 1e-12
        ),
        "ring_L_gt50_not_worse": (
            float(cd["sharp_length_ratio_gt_50"])
            <= float(bd["sharp_length_ratio_gt_50"]) + 1e-12
        ),
        "ring_L_gt100_folds_not_worse": (
            int(cd["dihedral_edge_count_gt_deg"]["100"])
            <= int(bd["dihedral_edge_count_gt_deg"]["100"])
        ),
    }

    result = {
        "version": VERSION,
        "scope": "ring_L proof only",
        "baseline": {
            "total_gt100_folds": int(b["digit_folds_over_100deg"]),
            "ring_L_gt35": float(bd["sharp_length_ratio_gt_35"]),
            "ring_L_gt50": float(bd["sharp_length_ratio_gt_50"]),
            "ring_L_gt100_folds": int(bd["dihedral_edge_count_gt_deg"]["100"]),
        },
        "candidate": {
            "total_gt100_folds": int(c["digit_folds_over_100deg"]),
            "ring_L_gt35": float(cd["sharp_length_ratio_gt_35"]),
            "ring_L_gt50": float(cd["sharp_length_ratio_gt_50"]),
            "ring_L_gt100_folds": int(cd["dihedral_edge_count_gt_deg"]["100"]),
        },
        "scope_movement": movement,
        "checks": checks,
        "pass": all(checks.values()),
        "next_if_pass": (
            "Checkpoint. Reproduce the same local topology strategy on ring_R, "
            "then pinky_L/pinky_R, auditing incrementally."
        ),
        "next_if_fail": (
            "Do not mirror this approach. Restore/checkpoint and revise only "
            "ring_L local edge flow/volume."
        ),
    }
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    if not result["pass"]:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
