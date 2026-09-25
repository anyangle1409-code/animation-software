"""Create (if needed) and open the prepared V15 hand candidate in Blender."""
from __future__ import annotations
import glob
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v15a_deep_hand_rebuild.blend"

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
    exe = find_blender()
    if not OUT.is_file():
        subprocess.run([
            exe, "--background", "--factory-startup",
            "--python", ROOT / "scripts" / "prepare_v15_deep_hand_blender.py",
        ], cwd=ROOT, check=True)
    if not OUT.is_file():
        raise SystemExit(f"V15 preparation did not create {OUT}")
    print("Opening prepared V15 candidate:", OUT, flush=True)
    subprocess.Popen([exe, str(OUT)], cwd=ROOT)

if __name__ == "__main__":
    main()
