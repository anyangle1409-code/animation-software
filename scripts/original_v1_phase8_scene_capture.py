#!/usr/bin/env python3
"""One-command future Phase 8 numeric material/presentation scene capture.

Read-only. Requires Phase 7 complete and same-candidate material provenance.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess

from original_v1_production_control import ROOT,CAND,build,digest,read
from original_v1_session_preflight import blender_path,process_info,repository_issues,run

CAPTURE="scripts/capture_original_v1_presentation_scene_blender.py"
VERIFY="scripts/original_v1_phase8_presentation.py"


def inside(path:Path)->Path:
    p=path.resolve()
    if not p.is_relative_to(ROOT.resolve()):raise ValueError("path must remain inside repository")
    return p


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("revision")
    ap.add_argument("--material-provenance",type=Path,required=True)
    ap.add_argument("--out-dir",type=Path,required=True)
    args=ap.parse_args()
    try:
        if not re.fullmatch(r"r\d+",args.revision):raise ValueError("numbered candidate revision required")
        provenance=inside(args.material_provenance);out=inside(args.out_dir)
        if not provenance.is_file():raise ValueError("material provenance missing")
        if out.exists():raise ValueError("Phase 8 output already exists; preserve evidence")

        control=read(ROOT,"ORIGINAL_V1_PRODUCTION_CONTROL.json")
        branch=run(["git","branch","--show-current"]);head=run(["git","rev-parse","HEAD"])
        live=run(["git","ls-remote","--exit-code","origin","refs/heads/"+control["branch"]]).split()[0]
        issues=repository_issues(branch,control["branch"],head,live,run(["git","status","--porcelain","--untracked-files=all"]))
        state,_=build(ROOT)
        if state.get("phases",{}).get("7",{}).get("state")!="complete":
            issues.append("Phase 7 incomplete; Phase 8 capture not eligible")
        blender=blender_path()
        if not blender:issues.append("Blender unavailable; set BLENDER_EXE")
        if process_info().get("conflicts"):issues.append("conflicting Blender/optimiser processes")
        if shutil.disk_usage(ROOT).free < 2*1024**3:issues.append("less than 2 GiB free for Phase 8 evidence")
        if issues:raise ValueError("; ".join(issues))

        candidate=ROOT/CAND/f"HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{args.revision}.blend"
        manifest=candidate.with_suffix(".json")
        if not candidate.is_file() or not manifest.is_file():raise ValueError("candidate Blend/manifest missing")
        data=json.loads(manifest.read_text(encoding="utf-8-sig"));sha=data.get("candidate_sha256")
        if data.get("candidate")!=candidate.name or digest(candidate)!=sha:raise ValueError("candidate identity differs")
        if state.get("last_known_candidate_sha256")!=sha:raise ValueError("candidate is not latest complete model state")
        prov=json.loads(provenance.read_text(encoding="utf-8-sig"))
        if prov.get("candidate_sha256")!=sha:raise ValueError("material provenance candidate differs")

        out.mkdir(parents=True)
        scene=out/"presentation_scene_capture.json";verified=out/"presentation_scene_verification.json"
        subprocess.run([str(blender),"--background","--factory-startup",str(candidate),"--python-exit-code","1",
                        "--python",CAPTURE,"--",str(scene)],cwd=ROOT,check=True)
        completed=subprocess.run(["python",VERIFY,"--scene-capture",str(scene),
                                  "--material-provenance",str(provenance),
                                  "--candidate-manifest",str(manifest),"--json-out",str(verified)],cwd=ROOT)
        print("PHASE 8 PRESENTATION FOLDER:",out)
        print("RENDER PLAN: ORIGINAL_V1_PHASE8_PRESENTATION_CAPTURE_PLAN.json")
        return completed.returncode
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError,subprocess.SubprocessError) as exc:
        print("STOP — "+str(exc));return 2

if __name__=="__main__":
    raise SystemExit(main())
