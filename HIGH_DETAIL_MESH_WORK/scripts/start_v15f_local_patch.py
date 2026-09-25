"""Prepare and open the V15f local ring/pinky patch candidate."""
from __future__ import annotations

import glob
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "v15f_deep_hand_rebuild"
BLEND = ROOT / f"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{VERSION}.blend"

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
    run([sys.executable, ROOT / "scripts" / "check_prepared_tooling.py"])
    run([sys.executable, ROOT / "scripts" / "preflight_v15.py"])

    exe = find_blender()
    if not BLEND.is_file():
        env = os.environ.copy()
        env["V15_VERSION"] = VERSION
        run([
            exe, "--background", "--factory-startup",
            "--python", ROOT / "scripts" / "prepare_v15_deep_hand_blender.py",
        ], env=env)

    run([
        exe, "--background", "--factory-startup",
        "--python", ROOT / "scripts" / "mark_v15f_hotspots_blender.py",
        "--", str(BLEND),
    ])

    print("Opening prepared V15f local-patch candidate:", BLEND, flush=True)
    subprocess.Popen([
        exe, str(BLEND),
        "--python", str(ROOT / "scripts" / "register_v15_blender_tools.py"),
    ], cwd=ROOT)

if __name__ == "__main__":
    main()
