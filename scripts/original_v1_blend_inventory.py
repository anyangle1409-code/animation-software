#!/usr/bin/env python3
"""Inventory local ORIGINAL-v1 Blender candidate files and identity/recovery state.

Local safety tool only. It never copies, uploads, deletes or edits a Blend file.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re

from original_v1_production_control import ROOT,CAND,build,digest,revision_key


def ledger_map(root:Path):
    path=root/"ORIGINAL_V1_CANDIDATE_LEDGER.json"
    if not path.is_file():return {}
    data=json.loads(path.read_text(encoding="utf-8"))
    return {row.get("revision"):row for row in data.get("candidates",[]) if isinstance(row,dict) and row.get("revision")}


def inventory(root:Path)->dict:
    state,_=build(root)
    ledger=ledger_map(root)
    rows=[]
    folder=root/CAND
    if folder.is_dir():
        for blend in sorted(folder.glob("HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r*.blend")):
            m=re.search(r"_CANDIDATE_(r\d+[a-z]?)\.blend$",blend.name,re.I)
            if not m:continue
            rev=m.group(1)
            actual=digest(blend)
            manifest_path=blend.with_suffix(".json")
            manifest=None;manifest_error=None
            if manifest_path.is_file():
                try:manifest=json.loads(manifest_path.read_text(encoding="utf-8-sig"))
                except (OSError,ValueError,TypeError,json.JSONDecodeError) as exc:manifest_error=str(exc)
            ledger_row=ledger.get(rev)
            manifest_ok=bool(manifest and manifest.get("candidate")==blend.name and manifest.get("candidate_sha256")==actual)
            ledger_ok=None if ledger_row is None else ledger_row.get("sha256")==actual
            if not manifest_path.is_file():status="MISSING_MANIFEST"
            elif manifest_error:status="INVALID_MANIFEST"
            elif not manifest_ok:status="MANIFEST_HASH_MISMATCH"
            elif ledger_row is not None and not ledger_ok:status="LEDGER_HASH_MISMATCH"
            else:status="IDENTITY_VERIFIED"
            stat=blend.stat()
            rows.append({
                "revision":rev,
                "path":blend.relative_to(root).as_posix(),
                "size_bytes":stat.st_size,
                "modified_utc":datetime.fromtimestamp(stat.st_mtime,timezone.utc).isoformat(),
                "sha256":actual,
                "manifest":{"path":manifest_path.relative_to(root).as_posix(),"exists":manifest_path.is_file(),
                            "parse_error":manifest_error,"matches_blend":manifest_ok},
                "ledger":{"present":ledger_row is not None,"matches_blend":ledger_ok},
                "is_current_complete":rev==state.get("current_candidate"),
                "is_incomplete_candidate":rev in state.get("incomplete_candidates",[]),
                "status":status,
            })
    rows.sort(key=lambda row:revision_key(row["revision"]))
    unresolved=[row for row in rows if row["status"]!="IDENTITY_VERIFIED"]
    current=state.get("current_candidate")
    expected=[]
    for revision in [current,*state.get("incomplete_candidates",[])]:
        if revision and revision not in expected:expected.append(revision)
    present={row["revision"] for row in rows}
    missing_expected=[revision for revision in expected if revision not in present]
    current_rows=[row for row in rows if row["revision"]==current]
    has_gaps=bool(unresolved or missing_expected)
    return {
        "schema_version":1,
        "status":"LOCAL_IDENTITY_GAPS" if has_gaps else "LOCAL_BLEND_IDENTITIES_VERIFIED",
        "production_approved":False,
        "current_candidate":current,
        "incomplete_candidates":state.get("incomplete_candidates",[]),
        "blend_count":len(rows),
        "current_blend_present":bool(current_rows),
        "missing_expected_revisions":missing_expected,
        "rows":rows,
        "unresolved_count":len(unresolved)+len(missing_expected),
        "notes":[
            "This is local file identity/recovery information, not remote backup.",
            "Blend binaries remain local under existing policy unless a separate project policy changes.",
            "A matching SHA/manifest proves identity only; it does not prove candidate quality or completion.",
            "This tool never copies, uploads, deletes or edits Blend files."
        ],
    }


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json-out",type=Path)
    args=ap.parse_args()
    try:
        result=inventory(ROOT)
        if args.json_out:
            out=args.json_out.resolve()
            if not out.is_relative_to(ROOT.resolve()):raise ValueError("output must remain inside repository")
            if out.exists():raise ValueError("inventory output collision")
            out.parent.mkdir(parents=True,exist_ok=True)
            out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
        print(json.dumps(result,indent=2))
        return 0 if result["unresolved_count"]==0 else 1
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc));return 2

if __name__=="__main__":
    raise SystemExit(main())
