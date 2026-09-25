"""Generate the V15f Stage-A ring/pinky visual proof and comparison board."""
from __future__ import annotations
import glob, os, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def find_blender():
    explicit = os.environ.get("BLENDER_EXE")
    if explicit and Path(explicit).is_file():
        return explicit
    found = shutil.which("blender")
    if found:
        return found
    if os.name == "nt":
        hits = sorted(glob.glob(r"C:\Program Files\Blender Foundation\Blender *\blender.exe"), reverse=True)
        if hits:
            return hits[0]
    raise SystemExit("Blender not found. Set BLENDER_EXE or add Blender to PATH.")

def main():
    exe = find_blender()
    subprocess.run([
        exe, "--background", "--factory-startup",
        "--python", ROOT / "scripts" / "render_v15f_stage_a_blender.py",
    ], cwd=ROOT, check=True)
    subprocess.run([
        sys.executable, ROOT / "scripts" / "make_v15f_stage_a_sheet.py",
    ], cwd=ROOT, check=True)
    print(ROOT / "renders_v15f_stage_a" / "V15F_V13E_STAGE_A_RING_PINKY_PROOF.jpg")

if __name__ == "__main__":
    main()
