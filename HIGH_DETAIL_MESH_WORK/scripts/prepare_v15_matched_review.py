"""Prepare true V13e-vs-V15 matched pose JSON for visual review.

The frozen V15 validation harness deliberately uses V8 as its mechanical
baseline. Visual acceptance, however, must compare the new hand directly to
V13e. This script copies V13e's already-generated candidate poses into the
V15 pose directory as the visual baseline without altering either asset.

Run after frozen candidate gates have been run for both versions.
"""
from __future__ import annotations
import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_VERSION = "v13e_fingertip_retopology"
DEFAULT_VERSION = "v15a_deep_hand_rebuild"

NEEDED = [
    "open_hand_review_candidate.json",
    "closed_fist_review_candidate.json",
    "dumbbell_bicep_curl_bottom_candidate.json",
    "push_up_bottom_candidate.json",
    "pull_up_peak_candidate.json",
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default=DEFAULT_VERSION)
    args = ap.parse_args()
    src = ROOT / "reports" / f"poses_{BASE_VERSION}"
    dst = ROOT / "reports" / f"poses_{args.version}"
    if not src.is_dir():
        raise SystemExit(
            f"Missing {src}. Run: python scripts/run_candidate_gates.py "
            f"--version {BASE_VERSION} --task hand"
        )
    if not dst.is_dir():
        raise SystemExit(
            f"Missing {dst}. Run frozen V15 gates first."
        )

    copied = []
    for name in NEEDED:
        source = src / name
        if not source.is_file():
            raise SystemExit(f"Missing V13e review pose: {source}")
        target = dst / name.replace("_candidate.json", "_baseline.json")
        payload = json.loads(source.read_text())
        payload["visualComparisonBaseline"] = "V13e"
        payload["visualComparisonCandidate"] = args.version
        target.write_text(json.dumps(payload))
        copied.append(target.name)

    manifest = {
        "baseline_version": BASE_VERSION,
        "candidate_version": args.version,
        "copied_pose_files": copied,
        "mechanical_validation_baseline_unchanged": "V8 / runtime 614033b",
        "purpose": "visual comparison only",
    }
    out = ROOT / "reports" / f"{args.version}_v13e_visual_baseline.json"
    out.write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))

if __name__ == "__main__":
    main()
