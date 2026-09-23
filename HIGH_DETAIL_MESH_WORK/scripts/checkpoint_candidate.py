"""Create a compact checkpoint manifest and review-note scaffold for a candidate.

Run from HIGH_DETAIL_MESH_WORK:
    python scripts/checkpoint_candidate.py --version v7_example

This is read-only with respect to the GLB/Blend assets. It writes only:
    reports/checkpoint_<version>.json
    REVIEW_<VERSION>.md   (only if that review file does not already exist)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent

def sha256(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def git(*args):
    try:
        return subprocess.check_output(
            ["git", *args], cwd=REPO, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return None

def glb_stats(path: Path):
    data = path.read_bytes()
    json_len = struct.unpack_from("<I", data, 12)[0]
    doc = json.loads(data[20:20 + json_len])
    primitive = doc["meshes"][0]["primitives"][0]
    pos = doc["accessors"][primitive["attributes"]["POSITION"]]["count"]
    tri = doc["accessors"][primitive["indices"]]["count"] // 3
    return {
        "body_vertices": pos,
        "body_triangles": tri,
        "nodes": len(doc.get("nodes", [])),
        "skins": len(doc.get("skins", [])),
        "animations": len(doc.get("animations", [])),
        "materials": len(doc.get("materials", [])),
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True)
    args = ap.parse_args()
    version = args.version

    files = {
        "dressed_glb": ROOT / f"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{version}.glb",
        "bare_glb": ROOT / f"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{version}_BARE.glb",
        "blend": ROOT / f"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{version}.blend",
    }
    missing = [str(p) for p in files.values() if not p.is_file()]
    if missing:
        raise SystemExit("Missing candidate artifacts:\n- " + "\n- ".join(missing))

    report = {
        "version": version,
        "branch": git("branch", "--show-current"),
        "head": git("rev-parse", "HEAD"),
        "artifacts": {
            key: {"path": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)}
            for key, path in files.items()
        },
        "glb": glb_stats(files["dressed_glb"]),
        "rig_baseline": {
            "freeze_commit": "19ca602ca2f2a821237dcf5b1b50c7906d86b0fe",
            "runtime_validation_commit": "614033b256d869230ea273522620467401b0bc71",
            "skeleton_id": "hgpt_canonical_v3",
            "canonical_bones": 63,
        },
        "expected_followup_logs": [
            f"reports/{version}_rig63_guards.log",
            f"reports/{version}_rig63_exercises.log",
            f"reports/exercise_validation_{version}.json",
        ],
    }
    out = ROOT / "reports" / f"checkpoint_{version}.json"
    out.write_text(json.dumps(report, indent=2))

    review = ROOT / f"REVIEW_{version.upper()}.md"
    if not review.exists():
        review.write_text(
f"""# {version} review candidate

## Scope
Describe exactly what changed and why.

## Geometry
- body vertices: {report['glb']['body_vertices']}
- body triangles: {report['glb']['body_triangles']}
- dressed SHA-256: {report['artifacts']['dressed_glb']['sha256']}
- bare SHA-256: {report['artifacts']['bare_glb']['sha256']}
- blend SHA-256: {report['artifacts']['blend']['sha256']}

## Preserved
List rig, weights, exercise, grip/contact, equipment, material or other invariants that were intentionally preserved.

## Validation
Record:
- candidate quick check
- focused guard result
- current all-exercise result against runtime source 614033b / hgpt_canonical_v3
- any region-specific audit
- visual review views inspected

## Remaining limitations
List anything intentionally not solved in this checkpoint.

## Promotion status
Review candidate only. Do not promote until explicitly approved.
"""
        )

    print(json.dumps(report, indent=2))
    print("checkpoint:", out)
    print("review:", review)

if __name__ == "__main__":
    main()
