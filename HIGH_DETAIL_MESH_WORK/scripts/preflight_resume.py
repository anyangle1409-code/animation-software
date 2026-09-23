"""Fast laptop resume preflight for the isolated high-detail mesh workspace."""

from __future__ import annotations

import glob
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v6_knee_seam.glb":
        "ff39e07735697d5423968a8ec1c05f2c6c68fced0d757ea1b4047096bc7a5306",
    "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v6_knee_seam_BARE.glb":
        "0170b3673d7a050e8aacd2683347cfa6dd000719dba0a6862c16bd7a4a5723e0",
    "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v6_knee_seam.blend":
        "2a2d0326129ce5c2555c596a49a281d655f33acfd7bbd9514cad3e759586a0df",
}
REQUIRED = [
    "LAPTOP_CONTINUATION_HANDOFF.md",
    "NEXT_ACTION.md",
    "REVIEW_V6_KNEE_SEAM.md",
    "REVIEW_V5_HANDS.md",
    "REVIEW_V4B.md",
    "reports/final_integrity_v6_knee_seam.json",
    "reports/hand_contact_guard_v5.json",
    "scripts/build_candidate_v6_knee_seam.py",
    "scripts/verify_v6_knee_seam.py",
]

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def run_git(*args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=ROOT.parent, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return "unavailable"

errors = []
print("HOME GYM PT mesh-work preflight")
print("=" * 34)
print("git branch:", run_git("branch", "--show-current"))
print("git HEAD:  ", run_git("rev-parse", "HEAD"))

for relative in REQUIRED:
    path = ROOT / relative
    if not path.is_file():
        errors.append(f"missing required file: {relative}")

for name, expected in EXPECTED.items():
    path = ROOT / name
    if not path.is_file():
        errors.append(f"missing V6 baseline artifact: {name}")
        continue
    actual = sha256(path)
    status = "OK" if actual == expected else "MISMATCH"
    print(f"{status:8} {name}")
    if actual != expected:
        errors.append(f"hash mismatch: {name}\n  expected {expected}\n  actual   {actual}")

integrity = ROOT / "reports/final_integrity_v6_knee_seam.json"
if integrity.is_file():
    data = json.loads(integrity.read_text())
    print("V6 body:  ", data.get("body_vertices"), "vertices /",
          data.get("body_triangles"), "triangles")
    print("degenerate:", data.get("degenerate_triangles"),
          " nonmanifold>2:", data.get("nonmanifold_edges_more_than_two_faces"))

blender = os.environ.get("BLENDER_EXE") or shutil.which("blender")
if not blender and os.name == "nt":
    matches = sorted(glob.glob(r"C:\\Program Files\\Blender Foundation\\Blender *\\blender.exe"), reverse=True)
    blender = matches[0] if matches else None
if blender and Path(blender).is_file():
    try:
        version = subprocess.check_output(
            [blender, "--version"], text=True, stderr=subprocess.STDOUT
        ).splitlines()[0]
    except Exception:
        version = "Blender found but version query failed"
    print("Blender:   ", version)
    print("Blender exe:", blender)
else:
    print("Blender:    not found; set BLENDER_EXE if it is installed outside PATH")

if errors:
    print("\nPRE-FLIGHT FAILED")
    for error in errors:
        print("-", error)
    raise SystemExit(1)

print("\nPRE-FLIGHT PASS")
print("Next: reproduce V6 before modelling, then work from WORK_START_HERE.md.")
