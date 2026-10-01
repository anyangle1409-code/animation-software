#!/usr/bin/env python3
"""Collect a compact, commit-friendly visual review set for one ORIGINAL v1 candidate.

Usage:
  python scripts/collect_original_v1_review_images.py r30

The full deformation runners already render every tested pose. This script only
copies a small deterministic subset into candidates/review/visual_<rev>/ so the
current model state can be reviewed from GitHub/phone without committing every
diagnostic render. It never edits candidate .blend files, evidence, thresholds,
or the pinned R2 baseline.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAND = ROOT / "ORIGINAL_V1_WORK" / "candidates"
RC = CAND / "repair_checks"
REVIEW = CAND / "review"

SELECTIONS = (
    ("neutral", "pose_neutral_front.png"),
    ("neutral", "pose_neutral_three_quarter.png"),
    ("shoulder", "pose_press_top_front.png"),
    ("shoulder", "pose_press_top_three_quarter.png"),
    ("shoulder", "pose_press_top_close_shoulder_a.png"),
    ("shoulder", "pose_pullup_top_front.png"),
    ("shoulder", "pose_pullup_top_close_hand_a.png"),
    ("hand", "pose_curl_peak_front.png"),
    ("hand", "pose_curl_peak_close_hand_a.png"),
    ("hand", "pose_curl_handle_front.png"),
    ("hand", "pose_curl_handle_close_hand_a.png"),
    ("pushup", "pose_pushup_bottom_three_quarter.png"),
    ("pushup", "pose_pushup_bottom_close_hand_a.png"),
    ("hip", "pose_lunge_front.png"),
    ("hip", "pose_lunge_side.png"),
    ("hip", "pose_lunge_three_quarter.png"),
    ("hip", "pose_lunge_close_hip_a.png"),
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_source(path: Path, candidate_sha: str):
    if not path.is_file():
        raise ValueError("missing render source manifest; regenerate actual evidence on laptop: " + str(path))
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("candidate_sha256") != candidate_sha:
        raise ValueError("render source candidate SHA mismatch")
    for row in data["images"]:
        name = Path(row["file"])
        if name.is_absolute() or len(name.parts) != 1:
            raise ValueError("invalid image filename")
        image_path = path.parent / name
        if not image_path.is_file() or sha256(image_path) != row["sha256"]:
            raise ValueError("render image SHA mismatch: " + str(image_path))
    report = path.parent / "pose_test_report.json"
    if not report.is_file() or sha256(report) != data.get("pose_report_sha256"):
        raise ValueError("render source pose report SHA mismatch")
    if not data.get("render_script_sha256") or not data.get("blender_version"):
        raise ValueError("render source lacks script/Blender identity")
    return data


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("revision", help="Candidate revision, for example r30")
    args = ap.parse_args()
    rev = args.revision.strip()
    if not rev.startswith("r") or not rev[1:].isdigit():
        raise SystemExit("revision must look like r30")

    out = REVIEW / f"visual_{rev}"
    if out.exists():
        raise SystemExit(f"refusing to overwrite existing visual review: {out}")
    candidate_manifest = CAND / f"HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{rev}.json"
    candidate_data = json.loads(candidate_manifest.read_text(encoding="utf-8-sig"))
    candidate_sha = candidate_data["candidate_sha256"]
    sources = {}
    for group, _ in SELECTIONS:
        if group not in sources:
            sources[group] = verify_source(RC / f"{group}_{rev}" / "render_source_manifest.json", candidate_sha)
    for group, name in SELECTIONS:
        if not any(x["file"] == name for x in sources[group]["images"]):
            raise ValueError("expected view missing from render source manifest: " + name)
    out.mkdir(parents=True)

    manifest = {
        "schema_version": 1,
        "candidate_revision": rev,
        "candidate_sha256": candidate_sha,
        "candidate_manifest_sha256": sha256(candidate_manifest),
        "source_manifests": [{"path": (RC / f"{g}_{rev}" / "render_source_manifest.json").relative_to(ROOT).as_posix(),
                              "sha256": sha256(RC / f"{g}_{rev}" / "render_source_manifest.json")} for g in sources],
        "owner_review": "pending",
        "blocking": False,
        "coverage": "compact repair snapshot; full milestone protocol remains separate",
        "purpose": "compact visual review copied from full deformation evidence",
        "production_approved": False,
        "files": [],
    }

    missing = []
    for group, name in SELECTIONS:
        src = RC / f"{group}_{rev}" / name
        if not src.exists():
            missing.append(str(src.relative_to(ROOT)))
            continue
        dst = out / f"{group}__{name}"
        shutil.copyfile(src, dst)
        manifest["files"].append(
            {
                "output": str(dst.relative_to(ROOT)).replace("\\", "/"),
                "source": str(src.relative_to(ROOT)).replace("\\", "/"),
                "sha256": sha256(dst),
                "bytes": dst.stat().st_size,
                "capture": next(x["capture"] for x in sources[group]["images"] if x["file"] == name),
            }
        )

    if missing:
        shutil.rmtree(out)
        raise SystemExit("missing expected review renders:\n  " + "\n  ".join(missing))

    (out / "visual_review_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"VISUAL REVIEW {rev}: {len(manifest['files'])} images -> {out}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise SystemExit("STOP — " + str(exc))
