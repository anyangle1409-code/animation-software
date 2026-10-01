#!/usr/bin/env python3
"""Launch a fail-closed read-only Blender smoke check on the current complete candidate."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess

from original_v1_production_control import ROOT,CAND,build,digest,read
from original_v1_session_preflight import blender_path,process_info,repository_issues,run

BLENDER_SCRIPT="scripts/smoke_original_v1_candidate_blender.py"


def main()->int:
    try:
        control=read(ROOT,"ORIGINAL_V1_PRODUCTION_CONTROL.json")
        branch=run(["git","branch","--show-current"]);head=run(["git","rev-parse","HEAD"])
        live=run(["git","ls-remote","--exit-code","origin","refs/heads/"+control["branch"]]).split()[0]
        issues=repository_issues(branch,control["branch"],head,live,run(["git","status","--porcelain","--untracked-files=all"]))
        if process_info().get("conflicts"):issues.append("conflicting Blender/optimiser processes")
        exe=blender_path()
        if not exe:issues.append("Blender unavailable; set BLENDER_EXE")
        state,_=build(ROOT)
        rev=state["current_candidate"]
        candidate=ROOT/CAND/f"HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{rev}.blend"
        manifest=candidate.with_suffix(".json")
        if not candidate.is_file() or not manifest.is_file():issues.append("current complete candidate Blend/manifest missing locally")
        else:
            data=json.loads(manifest.read_text(encoding="utf-8-sig"))
            if data.get("candidate")!=candidate.name or digest(candidate)!=data.get("candidate_sha256"):
                issues.append("current candidate Blend/manifest identity differs")
            if data.get("candidate_sha256")!=state.get("last_known_candidate_sha256"):
                issues.append("current local Blend differs from generated current candidate SHA")
        if issues:raise ValueError("; ".join(issues))
        completed=subprocess.run([str(exe),"--background","--factory-startup",str(candidate),
                                  "--python-exit-code","1","--python",BLENDER_SCRIPT],
                                 cwd=ROOT,text=True)
        return completed.returncode
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError,subprocess.SubprocessError) as exc:
        print("STOP — "+str(exc));return 2

if __name__=="__main__":
    raise SystemExit(main())
