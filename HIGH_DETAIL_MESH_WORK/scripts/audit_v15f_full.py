"""Run the general V15 Blender invariant audit on V15f."""
from __future__ import annotations
import glob,os,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BLEND=ROOT/"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v15f_deep_hand_rebuild.blend"
def find_blender():
    e=os.environ.get("BLENDER_EXE")
    if e and Path(e).is_file():return e
    f=shutil.which("blender")
    if f:return f
    if os.name=="nt":
        h=sorted(glob.glob(r"C:\Program Files\Blender Foundation\Blender *\blender.exe"),reverse=True)
        if h:return h[0]
    raise SystemExit("Blender not found")
if not BLEND.is_file():raise SystemExit(f"Missing V15f Blend: {BLEND}")
subprocess.run([
    find_blender(),"--background","--factory-startup",
    "--python",ROOT/"scripts"/"audit_v15_hand_blender.py","--",str(BLEND)
],cwd=ROOT,check=True)
