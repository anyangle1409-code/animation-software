#!/usr/bin/env python3
"""Read-only end-of-session safety check for ORIGINAL-v1 laptop work.

Reports whether work is clean/pushed, whether partial candidate bytes/evidence are
recoverable, and which exact actions remain before ending the session. Never commits,
pushes, fetches, deletes, saves Blender files or changes generated state.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess

from original_v1_production_control import ROOT,CAND,build,digest,read,revision_key
from original_v1_session_preflight import run

HANDOFF="docs/ORIGINAL_V1_O4_DEFORMATION_HANDOFF.md"
STATUS_CHECK=["python","scripts/build_original_v1_daily_status.py","--check"]


def sync_classification(local,remote,tree,left_right=None):
    if not remote:
        return "REMOTE_UNKNOWN"
    if local==remote:
        return "SYNCED_DIRTY" if tree else "SYNCED_CLEAN"
    if left_right is not None:
        left,right=left_right
        if left>0 and right==0:return "REMOTE_AHEAD"
        if right>0 and left==0:return "LOCAL_AHEAD_NEEDS_PUSH"
        if left>0 and right>0:return "DIVERGED"
    return "HEAD_DIFFERS_REMOTE"


def candidate_local_state(root:Path,revision:str):
    manifest_path=root/CAND/f"HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{revision}.json"
    result={"revision":revision,"manifest":manifest_path.relative_to(root).as_posix(),"manifest_exists":manifest_path.is_file(),
            "blend_exists":False,"blend_hash_matches":False,"candidate_sha256":None}
    if not manifest_path.is_file():return result
    try:
        manifest=json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        result["candidate_sha256"]=manifest.get("candidate_sha256")
        name=manifest.get("candidate")
        if isinstance(name,str):
            blend=manifest_path.parent/name
            result["blend"]=blend.relative_to(root).as_posix()
            result["blend_exists"]=blend.is_file()
            if blend.is_file() and isinstance(result["candidate_sha256"],str):
                result["blend_hash_matches"]=digest(blend)==result["candidate_sha256"]
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError):
        result["manifest_parse_error"]=True
    return result


def scan_local_blends(root:Path):
    rows=[]
    for blend in sorted((root/CAND).glob("HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r*.blend")):
        match=re.search(r"_CANDIDATE_(r\d+[a-z]?)\.blend$",blend.name,re.I)
        if not match:continue
        rev=match.group(1)
        manifest=blend.with_suffix(".json")
        row={"revision":rev,"path":blend.relative_to(root).as_posix(),"sha256":digest(blend),
             "manifest_exists":manifest.is_file(),"manifest_hash_matches":False}
        if manifest.is_file():
            try:
                data=json.loads(manifest.read_text(encoding="utf-8-sig"))
                row["manifest_hash_matches"]=data.get("candidate_sha256")==row["sha256"] and data.get("candidate")==blend.name
            except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError):
                pass
        rows.append(row)
    return rows


def assess(info):
    blockers=[];actions=[]
    if info["branch"]!=info["expected_branch"]:
        blockers.append("wrong model branch")
    sync=info["sync"]
    if sync=="LOCAL_AHEAD_NEEDS_PUSH":
        blockers.append("local commits have not been pushed");actions.append("push the current model branch after rechecking remote HEAD")
    elif sync=="REMOTE_AHEAD":
        blockers.append("remote branch has newer work");actions.append("reconcile/preserve newer remote work before ending or continuing")
    elif sync in ("DIVERGED","HEAD_DIFFERS_REMOTE","REMOTE_UNKNOWN"):
        blockers.append("local/remote branch state is unresolved");actions.append("inspect remote/local commit relationship without force-pushing")
    elif sync=="SYNCED_DIRTY":
        blockers.append("working tree has uncommitted/unknown files");actions.append("inspect and commit/preserve relevant session outputs")
    if info.get("working_tree"):
        if "working tree has uncommitted/unknown files" not in blockers:
            blockers.append("working tree has uncommitted/unknown files")
        if "inspect and commit/preserve relevant session outputs" not in actions:
            actions.append("inspect and commit/preserve relevant session outputs")
    if not info.get("generated_status_current"):
        blockers.append("generated status/dashboard is stale or invalid");actions.append("run build_original_v1_daily_status.py then --check")
    if not info.get("handoff_has_current_revision"):
        blockers.append("O4 handoff does not mention current complete revision");actions.append("update O4 handoff with current candidate/disposition/next action")
    if not info.get("handoff_has_next_action"):
        blockers.append("O4 handoff does not contain the evidence-selected next action");actions.append("record the exact next action in O4 handoff")

    partial=info.get("partial_candidates",[])
    if partial:
        for row in partial:
            if not row.get("manifest_exists"):
                blockers.append(row["revision"]+": partial candidate manifest missing")
                actions.append("preserve/create the candidate identity manifest without overwriting evidence")
            elif not row.get("blend_exists"):
                blockers.append(row["revision"]+": local partial Blend missing")
                actions.append("locate/preserve the partial Blend before session end")
            elif not row.get("blend_hash_matches"):
                blockers.append(row["revision"]+": partial Blend hash differs from manifest")
                actions.append("reconcile partial Blend/manifest identity; do not overwrite either")
            if not row.get("handoff_mentions"):
                blockers.append(row["revision"]+": partial candidate is not recorded in O4 handoff")
                actions.append("record partial candidate/recovery state in O4 handoff")
    orphan=[row for row in info.get("local_blends",[]) if not row.get("manifest_exists") or not row.get("manifest_hash_matches")]
    if orphan:
        blockers.append("local candidate Blend(s) lack matching committed-style identity manifests")
        actions.append("inspect local Blend(s) and preserve exact hashes/manifests before ending session")

    blockers=list(dict.fromkeys(blockers));actions=list(dict.fromkeys(actions))
    if blockers:
        status="NEEDS_ATTENTION_BEFORE_ENDING"
    elif partial:
        status="PARTIAL_WORK_PRESERVED"
    else:
        status="READY_TO_END_SESSION"
    return status,blockers,actions


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument("--json",action="store_true");args=ap.parse_args()
    try:
        control=read(ROOT,"ORIGINAL_V1_PRODUCTION_CONTROL.json")
        expected=control["branch"];branch=run(["git","branch","--show-current"]);head=run(["git","rev-parse","HEAD"])
        tree=run(["git","status","--porcelain","--untracked-files=all"])
        try:
            raw=run(["git","ls-remote","--exit-code","origin","refs/heads/"+expected]);remote=raw.split()[0] if raw else None
        except (OSError,subprocess.SubprocessError):
            remote=None
        left_right=None
        if remote and remote!=head:
            try:
                counts=run(["git","rev-list","--left-right","--count",remote+"..."+head]).split()
                if len(counts)==2:left_right=(int(counts[0]),int(counts[1]))
            except (OSError,ValueError,subprocess.SubprocessError):
                pass
        sync=sync_classification(head,remote,tree,left_right)
        state,_=build(ROOT)
        check=subprocess.run(STATUS_CHECK,cwd=ROOT,text=True,capture_output=True)
        handoff=(ROOT/HANDOFF).read_text(encoding="utf-8")
        current=state["current_candidate"];next_action=state["next_action"]
        handoff_has_current=current in handoff
        next_tokens=[str(next_action.get("action") or ""),str(next_action.get("command") or ""),str(next_action.get("work_package") or "")]
        handoff_has_next=any(token and token in handoff for token in next_tokens)

        partial=[]
        for revision in state.get("incomplete_candidates",[]):
            row=candidate_local_state(ROOT,revision);row["handoff_mentions"]=revision in handoff;partial.append(row)
        local_blends=scan_local_blends(ROOT)
        # Only flag local blends newer than/equal to the current revision where identity is unresolved.
        local_blends=[row for row in local_blends if revision_key(row["revision"])>=revision_key(current)]

        info={"expected_branch":expected,"branch":branch,"local_head":head,"remote_head":remote,
              "sync":sync,"working_tree":tree,"generated_status_current":check.returncode==0,
              "generated_status_check_stdout":check.stdout.strip(),"generated_status_check_stderr":check.stderr.strip(),
              "current_candidate":current,"candidate_state":state["candidate_state"],
              "next_action":next_action,"handoff":HANDOFF,
              "handoff_has_current_revision":handoff_has_current,"handoff_has_next_action":handoff_has_next,
              "partial_candidates":partial,"local_blends":local_blends,
              "pending_owner_reviews":state.get("pending_owner_reviews",[])}
        status,blockers,actions=assess(info)
        result={"status":status,"blockers":blockers,"closing_actions":actions,"information":info,
                "notes":[
                    "Routine pending owner review is non-blocking and does not prevent a clean session close.",
                    "Blend binaries remain local under existing policy; a verified local hash/manifest preserves identity, not remote binary backup.",
                    "This checker never commits, pushes, fetches, deletes or saves Blender files."
                ]}
        if args.json:print(json.dumps(result,indent=2))
        else:
            print(status)
            if blockers:
                print("BLOCKERS:");[print(" - "+x) for x in blockers]
            if actions:
                print("ACTIONS:");[print(" - "+x) for x in actions]
            print("NEXT:",next_action.get("action"),next_action.get("command") or next_action.get("work_package") or "")
        return 0 if status in ("READY_TO_END_SESSION","PARTIAL_WORK_PRESERVED") else 2
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError,subprocess.SubprocessError) as exc:
        print("STOP — "+str(exc));return 2

if __name__=="__main__":
    raise SystemExit(main())
