#!/usr/bin/env python3
"""Create a collision-safe local recovery copy of current/incomplete ORIGINAL-v1 Blend files.

Destination must be outside the repository. This is a local recovery copy only:
no network, no upload, no production evidence or approval.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess

from original_v1_production_control import ROOT,CAND,build,digest


def selected_revisions(state):
    rows=[state["current_candidate"],*state.get("incomplete_candidates",[])]
    out=[]
    for r in rows:
        if r not in out:out.append(r)
    return out


def collect(root:Path,state:dict):
    rows=[]
    for rev in selected_revisions(state):
        blend=root/CAND/f"HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{rev}.blend"
        manifest=blend.with_suffix(".json")
        if not blend.is_file():raise ValueError(f"{rev}: local Blend missing")
        if not manifest.is_file():raise ValueError(f"{rev}: adjacent manifest missing")
        data=json.loads(manifest.read_text(encoding="utf-8-sig"))
        sha=digest(blend)
        if data.get("candidate")!=blend.name or data.get("candidate_sha256")!=sha:
            raise ValueError(f"{rev}: Blend/manifest identity differs")
        rows.append({
            "revision":rev,
            "blend":blend,
            "manifest":manifest,
            "blend_sha256":sha,
            "manifest_sha256":digest(manifest),
            "size_bytes":blend.stat().st_size,
            "incomplete":rev in state.get("incomplete_candidates",[]),
        })
    return rows


def backup(root:Path,destination:Path):
    dest=destination.resolve()
    if dest.is_relative_to(root.resolve()):raise ValueError("backup destination must be outside repository")
    if dest.exists():raise ValueError("backup destination must be fresh; no overwrite")
    state,_=build(root)
    rows=collect(root,state)
    dest.mkdir(parents=True)
    copied=[]
    for row in rows:
        blend_out=dest/row["blend"].name
        manifest_out=dest/row["manifest"].name
        shutil.copy2(row["blend"],blend_out);shutil.copy2(row["manifest"],manifest_out)
        if digest(blend_out)!=row["blend_sha256"] or digest(manifest_out)!=row["manifest_sha256"]:
            raise ValueError(row["revision"]+": copied bytes failed hash verification")
        copied.append({
            "revision":row["revision"],
            "blend_file":blend_out.name,
            "blend_sha256":row["blend_sha256"],
            "manifest_file":manifest_out.name,
            "manifest_sha256":row["manifest_sha256"],
            "size_bytes":row["size_bytes"],
            "incomplete":row["incomplete"],
        })
    # Small text/json recovery context only.
    context_files=[
        "ORIGINAL_V1_HIGH_DETAIL_STATUS.json",
        "ORIGINAL_V1_CANDIDATE_LEDGER.json",
        "docs/ORIGINAL_V1_O4_DEFORMATION_HANDOFF.md",
        "ORIGINAL_V1_EXECUTION_ORCHESTRATION.json",
    ]
    context=[]
    for rel in context_files:
        src=root/rel
        if src.is_file():
            name=rel.replace("/","__")
            dst=dest/name;shutil.copy2(src,dst)
            context.append({"source":rel,"backup_file":name,"sha256":digest(dst)})
    result={
        "schema_version":1,
        "status":"LOCAL_RECOVERY_BACKUP_VERIFIED",
        "production_approved":False,
        "source_repository":str(root.resolve()),
        "source_branch":subprocess.check_output(["git","branch","--show-current"],cwd=root,text=True).strip(),
        "source_git_commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip(),
        "current_candidate":state["current_candidate"],
        "incomplete_candidates":state.get("incomplete_candidates",[]),
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "candidate_files":copied,
        "context_files":context,
        "notes":[
            "Local recovery copy only; not a production artifact or repository evidence.",
            "No source file is edited or deleted.",
            "Destination is required to be outside the repository and fresh.",
            "Copied Blend/manifest bytes are re-hashed after copy."
        ],
    }
    (dest/"backup_manifest.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    return result


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("fresh_backup_directory",type=Path)
    args=ap.parse_args()
    try:
        result=backup(ROOT,args.fresh_backup_directory)
        print(json.dumps(result,indent=2))
        return 0
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError,subprocess.SubprocessError,shutil.Error) as exc:
        print("STOP - "+str(exc));return 2

if __name__=="__main__":
    raise SystemExit(main())
