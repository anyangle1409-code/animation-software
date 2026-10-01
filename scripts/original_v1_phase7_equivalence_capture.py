#!/usr/bin/env python3
"""One-command future Phase 7 bare/dressed underlying-body equivalence capture."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess

from original_v1_production_control import ROOT,CAND,build,digest,read
from original_v1_session_preflight import blender_path,process_info,repository_issues,run

CAPTURE="scripts/capture_original_v1_bare_dressed_equivalence_blender.py"
VERIFY="scripts/original_v1_bare_dressed_equivalence.py"


def inside(path:Path)->Path:
    p=path.resolve()
    if not p.is_relative_to(ROOT.resolve()):raise ValueError("path must remain inside repository")
    return p


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("revision")
    ap.add_argument("--out-dir",type=Path,required=True)
    args=ap.parse_args()
    try:
        if not re.fullmatch(r"r\d+",args.revision):raise ValueError("numbered candidate revision required")
        out=inside(args.out_dir)
        if out.exists():raise ValueError("Phase 7 equivalence output exists; preserve evidence")

        control=read(ROOT,"ORIGINAL_V1_PRODUCTION_CONTROL.json")
        branch=run(["git","branch","--show-current"]);head=run(["git","rev-parse","HEAD"])
        live=run(["git","ls-remote","--exit-code","origin","refs/heads/"+control["branch"]]).split()[0]
        issues=repository_issues(branch,control["branch"],head,live,run(["git","status","--porcelain","--untracked-files=all"]))
        state,_=build(ROOT)
        if state.get("phases",{}).get("6",{}).get("state")!="complete":
            issues.append("Phase 6 incomplete; Phase 7 equivalence capture not eligible")
        blender=blender_path()
        if not blender:issues.append("Blender unavailable; set BLENDER_EXE")
        if process_info().get("conflicts"):issues.append("conflicting Blender/optimiser processes")
        if shutil.disk_usage(ROOT).free<2*1024**3:issues.append("less than 2 GiB free for equivalence evidence")
        if issues:raise ValueError("; ".join(issues))

        candidate=ROOT/CAND/f"HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{args.revision}.blend"
        manifest=candidate.with_suffix(".json")
        if not candidate.is_file() or not manifest.is_file():raise ValueError("candidate Blend/manifest missing")
        data=json.loads(manifest.read_text(encoding="utf-8-sig"));sha=data.get("candidate_sha256")
        if data.get("candidate")!=candidate.name or digest(candidate)!=sha:raise ValueError("candidate identity differs")
        if state.get("last_known_candidate_sha256")!=sha:raise ValueError("candidate is not latest complete model state")

        out.mkdir(parents=True)
        capture_dir=out/"capture"
        subprocess.run([str(blender),"--background","--factory-startup",str(candidate),"--python-exit-code","1",
                        "--python",CAPTURE,"--",str(capture_dir),args.revision],cwd=ROOT,check=True)
        report=capture_dir/"bare_dressed_equivalence.json"
        verified=out/"verified_bare_dressed_equivalence.json"
        completed=subprocess.run(["python",VERIFY,str(report),"--revision",args.revision,"--json-out",str(verified)],cwd=ROOT)
        print("PHASE 7 BARE/DRESSED EQUIVALENCE FOLDER:",out)
        return completed.returncode
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError,subprocess.SubprocessError) as exc:
        print("STOP — "+str(exc));return 2

if __name__=="__main__":
    raise SystemExit(main())
