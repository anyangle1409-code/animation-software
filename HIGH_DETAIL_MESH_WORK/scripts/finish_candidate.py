"""Run the standard post-edit workflow for one candidate.

Usage:
    python scripts/finish_candidate.py --version v7_knee --task knee
    python scripts/finish_candidate.py --version v8_hands --task hand
    python scripts/finish_candidate.py --version v9_skin --task material

This orchestrates existing read-only/validation helpers; it does not promote
or merge a candidate.
"""

from __future__ import annotations
import argparse,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def run(args):
    print("+"," ".join(str(x) for x in args),flush=True)
    subprocess.run([str(x) for x in args],cwd=ROOT,check=True)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--version",required=True)
    ap.add_argument("--task",required=True,choices=("knee","hand","material","shoulder"))
    ap.add_argument("--overhead",action="store_true")
    args=ap.parse_args()

    candidate=ROOT/f"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{args.version}.glb"
    bare=ROOT/f"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{args.version}_BARE.glb"
    blend=ROOT/f"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{args.version}.blend"
    if not candidate.is_file():
        raise SystemExit(f"Missing dressed candidate GLB: {candidate}")
    if not blend.is_file():
        raise SystemExit(f"Missing editable candidate Blend: {blend}")
    if not bare.is_file():
        print("Bare GLB missing; creating it from the dressed candidate.")
        run([sys.executable,ROOT/"scripts"/"make_bare_variant.py",args.version])

    run([sys.executable,ROOT/"scripts"/"run_candidate_gates.py","--version",args.version,"--task",args.task])
    if args.task=="knee":
        run([sys.executable,ROOT/"scripts"/"audit_knee_topology_candidate.py",candidate])
    elif args.task=="hand":
        run([sys.executable,ROOT/"scripts"/"guard_hand_floor_vertices.py",candidate,"--strict"])

    cmd=[sys.executable,ROOT/"scripts"/"prepare_review_pack.py","--version",args.version]
    if args.overhead or args.task=="shoulder":cmd.append("--overhead")
    run(cmd)
    run([sys.executable,ROOT/"scripts"/"checkpoint_candidate.py","--version",args.version])
    print("\nFINISH WORKFLOW PASS")
    print("Candidate remains review-only. Inspect the generated contact sheets before acceptance.")

if __name__=="__main__":
    main()
