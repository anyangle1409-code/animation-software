"""Update observed Work meters and finish the active usage sample."""
from __future__ import annotations
import argparse
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SET=ROOT/"scripts"/"set_ai_budget.py"
END=ROOT/"scripts"/"end_work_usage_sample.py"

ap=argparse.ArgumentParser()
ap.add_argument("window_after",type=float)
ap.add_argument("week_after",type=float,nargs="?",default=None)
ap.add_argument("--notes",default="")
ap.add_argument("--credits-used",type=float,default=None)
args=ap.parse_args()

subprocess.run(
    [sys.executable,str(SET),"work_window",str(args.window_after)],
    cwd=ROOT,check=True,
)
if args.week_after is not None:
    subprocess.run(
        [sys.executable,str(SET),"work_week",str(args.week_after)],
        cwd=ROOT,check=True,
    )

cmd=[sys.executable,str(END),str(args.window_after)]
if args.week_after is not None:
    cmd += ["--week-after",str(args.week_after)]
if args.credits_used is not None:
    cmd += ["--credits-used",str(args.credits_used)]
if args.notes:
    cmd += ["--notes",args.notes]
raise SystemExit(subprocess.run(cmd,cwd=ROOT).returncode)
