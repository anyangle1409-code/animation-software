"""Run the V15f Blender invariant audit and enforce the Stage-A ring/pinky gate."""
from __future__ import annotations

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
OUT = ROOT / "reports" / "v15f_stage_a_gate.json"
DIGITS = ("ring_L", "ring_R", "pinky_L", "pinky_R")

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

    if not AUDIT.is_file():
        raise SystemExit(f"Audit report not generated: {AUDIT}")

    report = json.loads(AUDIT.read_text(encoding="utf-8"))
    baseline = report["baseline_topology"]
    candidate = report["candidate_topology"]

    failures = []
    per_digit = {}
    movement = report.get("per_digit_original_movement_vs_v13e", {})

    if not report.get("pass"):
        failures.append("General V15 invariant audit failed.")

    baseline_total = int(baseline["digit_folds_over_100deg"])
    candidate_total = int(candidate["digit_folds_over_100deg"])
    if candidate_total > baseline_total:
        failures.append(
            f"Total >100deg digit folds worsened: {baseline_total} -> {candidate_total}."
        )

    for untouched in ("index_L", "index_R", "middle_L", "middle_R"):
        item = movement.get(untouched, {})
        if float(item.get("max_move_mm", 0.0)) > 1e-6:
            failures.append(
                f"{untouched}: moved during ring/pinky Stage A "
                f"({item.get('max_move_mm')} mm)."
            )

    for digit in DIGITS:
        b = baseline["per_digit_surface"][digit]
        c = candidate["per_digit_surface"][digit]
        b35 = float(b["sharp_length_ratio_gt_35"])
        c35 = float(c["sharp_length_ratio_gt_35"])
        b50 = float(b["sharp_length_ratio_gt_50"])
        c50 = float(c["sharp_length_ratio_gt_50"])
        b100 = int(b["dihedral_edge_count_gt_deg"]["100"])
        c100 = int(c["dihedral_edge_count_gt_deg"]["100"])

        digit_failures = []
        if c35 > b35 + 1e-12:
            digit_failures.append(
                f">35deg sharp-length ratio worsened {b35:.10f} -> {c35:.10f}"
            )
        if c50 > b50 + 1e-12:
            digit_failures.append(
                f">50deg sharp-length ratio worsened {b50:.10f} -> {c50:.10f}"
            )
        if c100 > b100:
            digit_failures.append(
                f">100deg fold edges worsened {b100} -> {c100}"
            )

        per_digit[digit] = {
            "baseline_sharp_ratio_gt35": b35,
            "candidate_sharp_ratio_gt35": c35,
            "delta_sharp_ratio_gt35": c35 - b35,
            "baseline_sharp_ratio_gt50": b50,
            "candidate_sharp_ratio_gt50": c50,
            "delta_sharp_ratio_gt50": c50 - b50,
            "baseline_folds_gt100": b100,
            "candidate_folds_gt100": c100,
            "pass": not digit_failures,
            "failures": digit_failures,
        }
        for item in digit_failures:
            failures.append(f"{digit}: {item}")

    surface_fingerprints = {
        digit: candidate["per_digit_surface"][digit].get("surface_fingerprint_sha256")
        for digit in DIGITS
    }

    result = {
        "version": VERSION,
        "general_invariant_pass": bool(report.get("pass")),
        "surface_fingerprints_sha256": surface_fingerprints,
        "baseline_total_folds_gt100": baseline_total,
        "candidate_total_folds_gt100": candidate_total,
        "per_digit": per_digit,
        "scope_movement": movement,
        "pass": not failures,
        "failures": failures,
        "next_if_pass": (
            "Checkpoint ring/pinky and proceed to Stage B index/middle inspection."
        ),
        "next_if_fail": (
            "Keep work local to ring/pinky. Repair hotspot topology before touching index/middle."
        ),
    }
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    subprocess.run([
        sys.executable, ROOT / "scripts" / "write_v15f_handoff.py",
    ], cwd=ROOT, check=False)

    if failures:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
