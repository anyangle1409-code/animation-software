"""Create a new editable candidate Blender file from accepted V8 knee geometry.

This does not create a git branch, alter V8, or export/promote anything. The
accepted V8 Blend already carries candidate-side audit selection groups.

Usage:
    python scripts/start_candidate.py --version v9_hand_anatomy
"""

from __future__ import annotations
import argparse,hashlib,json,shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy.blend"

def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--version",required=True);args=ap.parse_args()
    version=args.version.strip()
    if not version or any(c in version for c in r'\/:*?"<>| '):
        raise SystemExit("Use a simple version suffix such as v9_hand_anatomy")
    target=ROOT/f"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{version}.blend"
    if target.exists():
        raise SystemExit(f"Refusing to overwrite existing candidate: {target}")
    if not BASE.is_file():raise SystemExit(f"Missing accepted V8 Blender source: {BASE}")
    shutil.copy2(BASE,target)
    report={
      "version":version,
      "base":BASE.name,
      "base_sha256":digest(BASE),
      "candidate_blend":target.name,
      "candidate_sha256":digest(target),
      "note":"Exact separate copy of accepted V8 geometry; candidate remains review-only."
    }
    out=ROOT/"reports"/f"start_{version}.json";out.write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    print("\nOpen this in Blender:",target)

if __name__=="__main__":
    main()
