"""Frozen validation + direct V13e matched visual review for a versioned V15 candidate."""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VERSION = "v15a_deep_hand_rebuild"
BASE_VERSION = "v13e_fingertip_retopology"

def run(cmd, env=None):
    print("+", " ".join(str(x) for x in cmd), flush=True)
    subprocess.run([str(x) for x in cmd], cwd=ROOT, env=env, check=True)

def blender():
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

def label_for(version: str) -> str:
    m = re.match(r"v(\d+)([a-z]?)", version, re.I)
    if not m:
        return version.upper()
    return f"V{m.group(1)}{m.group(2)}"

def need_v13_poses():
    root = ROOT / "reports" / f"poses_{BASE_VERSION}"
    names = [
        "open_hand_review_candidate.json",
        "closed_fist_review_candidate.json",
        "dumbbell_bicep_curl_bottom_candidate.json",
        "push_up_bottom_candidate.json",
        "pull_up_peak_candidate.json",
    ]
    return not all((root / x).is_file() for x in names)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default=DEFAULT_VERSION)
    args = ap.parse_args()
    version = args.version
    candidate_label = label_for(version)

    candidate_blend = ROOT / f"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{version}.blend"
    candidate_glb = ROOT / f"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{version}.glb"
    if not candidate_blend.is_file() or not candidate_glb.is_file():
        raise SystemExit("Candidate Blend and dressed GLB must exist before finishing.")

    exe = blender()
    run([
        exe, "--background", "--factory-startup",
        "--python", ROOT / "scripts" / "audit_v15_hand_blender.py",
        "--", str(candidate_blend),
    ])

    run([
        sys.executable, ROOT / "scripts" / "finish_candidate.py",
        "--version", version, "--task", "hand",
    ])

    if need_v13_poses():
        run([
            sys.executable, ROOT / "scripts" / "run_candidate_gates.py",
            "--version", BASE_VERSION, "--task", "hand",
        ])

    run([
        sys.executable, ROOT / "scripts" / "prepare_v15_matched_review.py",
        "--version", version,
    ])

    env = os.environ.copy()
    env["RENDER_VERSION"] = version
    renderer = ROOT / "scripts" / "render_candidate_review.py"
    run([exe, "--background", "--factory-startup", "--python", renderer, "--", "hand_studies"], env)
    run([exe, "--background", "--factory-startup", "--python", renderer, "--", "hands_compare"], env)
    run([exe, "--background", "--factory-startup", "--python", renderer, "--", "pullup_hands"], env)
    run([
        sys.executable, ROOT / "scripts" / "make_v15_hand_review_sheets.py",
        "--version", version,
        "--candidate-label", candidate_label,
        "--baseline-label", "V13e",
    ])

    run([
        exe, "--background", "--factory-startup",
        "--python", ROOT / "scripts" / "audit_hand_seams.py",
        "--", BASE_VERSION, version,
    ])

    run([
        sys.executable, ROOT / "scripts" / "analyze_v15_visual_change.py",
        "--version", version,
    ])

    status = {
        "version": version,
        "candidate_label": candidate_label,
        "frozen_runtime": "614033b256d869230ea273522620467401b0bc71",
        "visual_baseline": "V13e",
        "blender_invariant_audit": "PASS",
        "frozen_candidate_gates": "PASS",
        "protected_floor_guard": "PASS",
        "matched_review_rendering": "PASS",
        "hand_seam_audit": "COMPLETE",
        "visual_change_metrics": "COMPLETE",
        "pass": True,
        "remaining": "latest-source integration and human/AI visual anatomy verdict",
    }
    status_path = ROOT / "reports" / f"{version}_frozen_pipeline_status.json"
    status_path.write_text(json.dumps(status, indent=2))

    print("\nV15 FROZEN + MATCHED VISUAL WORKFLOW PASS")
    print("candidate:", version)
    print("Still required before acceptance: latest-source integration validation.")
    print("Do not refit grips or promote the candidate yet.")

if __name__ == "__main__":
    main()
