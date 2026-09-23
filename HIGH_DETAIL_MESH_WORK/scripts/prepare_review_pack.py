"""Generate standard visual-review renders and contact sheets for a candidate.

Requires pose JSON from run_candidate_gates.py and Blender.

Usage:
    python scripts/prepare_review_pack.py --version v7_example
    python scripts/prepare_review_pack.py --version v7_example --overhead
"""

from __future__ import annotations
import argparse,glob,os,shutil,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def find_blender():
    explicit=os.environ.get("BLENDER_EXE")
    if explicit and Path(explicit).is_file():return explicit
    found=shutil.which("blender")
    if found:return found
    if os.name=="nt":
        matches=sorted(glob.glob(r"C:\Program Files\Blender Foundation\Blender *\blender.exe"),reverse=True)
        if matches:return matches[0]
    return None

def run(cmd,env=None):
    print("+"," ".join(str(x) for x in cmd),flush=True)
    subprocess.run([str(x) for x in cmd],cwd=ROOT,env=env,check=True)

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--version",required=True)
    ap.add_argument("--overhead",action="store_true")
    args=ap.parse_args()
    poses=ROOT/"reports"/f"poses_{args.version}"
    if not poses.is_dir():
        raise SystemExit(f"Missing {poses}. Run scripts/run_candidate_gates.py first.")
    blender=find_blender()
    if not blender:
        raise SystemExit("Blender not found. Set BLENDER_EXE to blender.exe or add Blender to PATH.")
    env=os.environ.copy();env["RENDER_VERSION"]=args.version
    renderer=ROOT/"scripts"/"render_candidate_review.py"
    run([blender,"--background","--factory-startup","--python",renderer,"--","all"],env)
    run([blender,"--background","--factory-startup","--python",renderer,"--","hands"],env)
    run([blender,"--background","--factory-startup","--python",renderer,"--","knees"],env)
    if args.overhead:
        run([blender,"--background","--factory-startup","--python",renderer,"--","target"],env)
    run([sys.executable,ROOT/"scripts"/"make_review_sheet_generic.py","--version",args.version],env)
    print("REVIEW PACK READY:",ROOT/f"renders_{args.version}")

if __name__=="__main__":
    main()
