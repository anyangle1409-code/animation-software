"""One-command post-export V15 hand workflow.

This intentionally keeps current-source integration separate. It runs:
1. Blender-side invariant audit against V13e.
2. Existing frozen 614033b candidate finish workflow.
3. V13e frozen hand poses if not already available.
4. True V13e-vs-V15 matched hand renders and comparison boards.

It never promotes or merges a candidate.
"""
from __future__ import annotations
import glob
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "v15a_deep_hand_rebuild"
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
    candidate_blend = ROOT / f"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{VERSION}.blend"
    candidate_glb = ROOT / f"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{VERSION}.glb"
    if not candidate_blend.is_file() or not candidate_glb.is_file():
        raise SystemExit("V15 Blend and dressed GLB must exist before finishing.")

    exe = blender()
    run([
        exe, "--background", str(candidate_blend),
        "--python", ROOT / "scripts" / "audit_v15_hand_blender.py",
        "--", str(candidate_blend),
    ])

    # Reuse the established frozen finish workflow: bare export if needed,
    # quick structural check, 614033b guards/exercises, generic review, checkpoint.
    run([
        sys.executable, ROOT / "scripts" / "finish_candidate.py",
        "--version", VERSION, "--task", "hand",
    ])

    # Produce V13e posed baselines once. The validation pin remains V8/614033b;
    # these copied poses are only for the direct visual comparison.
    if need_v13_poses():
        run([
            sys.executable, ROOT / "scripts" / "run_candidate_gates.py",
            "--version", BASE_VERSION, "--task", "hand",
        ])

    run([
        sys.executable, ROOT / "scripts" / "prepare_v15_matched_review.py",
        "--version", VERSION,
    ])

    env = os.environ.copy()
    env["RENDER_VERSION"] = VERSION
    renderer = ROOT / "scripts" / "render_candidate_review.py"
    run([exe, "--background", "--factory-startup", "--python", renderer, "--", "hand_studies"], env)
    run([exe, "--background", "--factory-startup", "--python", renderer, "--", "hands_compare"], env)
    # Pull-up needs the side view for the V15 comparison set.
    run([exe, "--background", "--factory-startup", "--python", renderer, "--", "pullup_hands"], env)
    run([
        sys.executable, ROOT / "scripts" / "make_v15_hand_review_sheets.py",
        "--version", VERSION,
    ])

    # Direct topology/seam comparison against V13e using the matched open pose.
    run([
        exe, "--background", "--factory-startup",
        "--python", ROOT / "scripts" / "audit_hand_seams.py",
        "--", BASE_VERSION, VERSION,
    ])

    # Quantify whether the candidate visibly moved enough to avoid another
    # V14e-style "technically large, visually marginal" checkpoint.
    run([
        sys.executable, ROOT / "scripts" / "analyze_v15_visual_change.py",
        "--version", VERSION,
    ])

    status = {
        "version": VERSION,
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
    status_path = ROOT / "reports" / f"{VERSION}_frozen_pipeline_status.json"
    status_path.write_text(json.dumps(status, indent=2))

    print("\nV15 FROZEN + MATCHED VISUAL WORKFLOW PASS")
    print("Still required before acceptance: latest-source integration validation.")
    print("Do not refit grips or promote the candidate yet.")

if __name__ == "__main__":
    main()
