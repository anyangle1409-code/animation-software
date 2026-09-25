"""Export V15 dressed GLB from the saved Blender candidate using the proven V11+ packer.

The packer retains V8's stable original GLB vertex prefix, rig, nodes, skins,
materials, shorts and metadata; it adds/rebuilds only the body primitive arrays
from the V15 Blender topology. All original v8_source_id vertices must survive.
"""
from __future__ import annotations
import glob
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "v15a_deep_hand_rebuild"
BLEND = ROOT / f"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{VERSION}.blend"
TARGET = ROOT / f"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{VERSION}.glb"
REPORT = ROOT / "reports" / f"build_{VERSION}_glb.json"

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

def run(cmd, env=None):
    print("+", " ".join(str(x) for x in cmd), flush=True)
    subprocess.run([str(x) for x in cmd], cwd=ROOT, env=env, check=True)

def main():
    if not BLEND.is_file():
        raise SystemExit(f"Missing saved V15 Blend: {BLEND}")
    if TARGET.exists():
        raise SystemExit(
            f"Refusing to overwrite existing {TARGET.name}. "
            "Preserve the attempt and use a new candidate version if rebuilding."
        )
    exe = find_blender()

    # Fail before packing if protected/non-digit/stable-ID invariants were broken.
    run([
        exe, "--background", "--factory-startup",
        "--python", ROOT / "scripts" / "audit_v15_hand_blender.py",
        "--", str(BLEND),
    ])

    env = os.environ.copy()
    env["BLEND"] = str(BLEND)
    env["TARGET"] = str(TARGET)
    env["REPORT"] = str(REPORT)
    run([
        exe, "--background", "--factory-startup",
        "--python", ROOT / "scripts" / "pack_v11_hand_glb.py",
    ], env=env)

    print("\nV15 DRESSED GLB EXPORTED:", TARGET)
    print("Bare variant will be created by the finish workflow.")

if __name__ == "__main__":
    main()
