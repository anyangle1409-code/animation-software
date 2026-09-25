"""Generate matched V15f Stage-B visual proof for one digit."""
from __future__ import annotations
import argparse,glob,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ALLOWED=("index_L","index_R","middle_L","middle_R")
def blender():
    e=os.environ.get("BLENDER_EXE")
    if e and Path(e).is_file():return e
    f=shutil.which("blender")
    if f:return f
    if os.name=="nt":
        h=sorted(glob.glob(r"C:\Program Files\Blender Foundation\Blender *\blender.exe"),reverse=True)
        if h:return h[0]
    raise SystemExit("Blender not found")
def main():
    ap=argparse.ArgumentParser();ap.add_argument("digit",choices=ALLOWED);a=ap.parse_args()
    subprocess.run([blender(),"--background","--factory-startup","--python",
        ROOT/"scripts"/"render_v15f_stage_b_digit_blender.py","--",a.digit],cwd=ROOT,check=True)
    subprocess.run([sys.executable,ROOT/"scripts"/"make_v15f_stage_b_digit_sheet.py",a.digit],cwd=ROOT,check=True)
if __name__=="__main__":main()
