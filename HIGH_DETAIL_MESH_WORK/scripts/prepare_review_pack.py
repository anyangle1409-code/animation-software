"""Generate standard visual-review renders and contact sheets for a candidate.

Requires pose JSON from run_candidate_gates.py and Blender on PATH.

Usage:
    python scripts/prepare_review_pack.py --version v7_example
    python scripts/prepare_review_pack.py --version v7_example --overhead
"""

from __future__ import annotations
import argparse,os,shutil,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

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
    blender=shutil.which("blender")
    if not blender:
        raise SystemExit("Blender not found on PATH")
    env=os.environ.copy();env["RENDER_VERSION"]=args.version
    renderer=ROOT/"scripts"/"render_review_v3.py"
    run([blender,"--background","--factory-startup","--python",renderer,"--","all"],env)
    run([blender,"--background","--factory-startup","--python",renderer,"--","hands"],env)
    run([blender,"--background","--factory-startup","--python",renderer,"--","knees"],env)
    if args.overhead:
        run([blender,"--background","--factory-startup","--python",renderer,"--","target"],env)
    run([sys.executable,ROOT/"scripts"/"make_review_sheet_generic.py","--version",args.version],env)
    print("REVIEW PACK READY:",ROOT/f"renders_{args.version}")

if __name__=="__main__":
    main()
