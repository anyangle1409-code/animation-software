#!/usr/bin/env python3
"""Validate ORIGINAL-v1 real-human surface visual evidence requirements."""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VISUAL=ROOT/"ORIGINAL_V1_SURFACE_VISUAL_EVIDENCE_REQUIREMENTS.json"
MASTER=ROOT/"ORIGINAL_V1_HUMAN_BODY_MASTER_PLAN.json"
HUMAN=ROOT/"ORIGINAL_V1_HUMAN_EVIDENCE_MANIFEST.json"

def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def validate(data,master,human):
    if data.get("schema_version")!=1:
        raise ValueError("schema_version must be 1")
    if data.get("status")!="SURFACE_VISUAL_EVIDENCE_REQUIREMENTS_ACTIVE":
        raise ValueError("unexpected visual-evidence status")
    if data.get("production_approved") is not False:
        raise ValueError("visual evidence requirements may not claim production approval")
    required_states=set(data.get("required_states") or [])
    if required_states!={"neutral","lengthened_or_elevated","compressed_or_loaded","intermediate_transition","return_transition"}:
        raise ValueError("required visual states differ")
    expected={x["id"] for x in master.get("body_regions",[])}
    rows=data.get("regions") or []
    ids=[r.get("id") for r in rows]
    if set(ids)!=expected or len(ids)!=len(set(ids)):
        raise ValueError("visual evidence must cover every master body region exactly once")
    evidence_ids={e["id"] for e in human.get("entries",[])}
    allowed_states={"complete","partial","missing"}
    for row in rows:
        rid=row["id"]
        if row.get("state") not in allowed_states:
            raise ValueError(f"{rid}: invalid state")
        refs=row.get("current_visual_evidence_ids") or []
        unknown=set(refs)-evidence_ids
        if unknown:
            raise ValueError(f"{rid}: unknown visual evidence ids {sorted(unknown)}")
        if row["state"]=="complete":
            if row.get("needs"):
                raise ValueError(f"{rid}: complete region cannot retain needs")
            if len(refs)<2:
                raise ValueError(f"{rid}: complete visual region requires multiple references")
        else:
            if not row.get("needs"):
                raise ValueError(f"{rid}: incomplete region must state remaining needs")
    summary=data.get("summary") or {}
    counts={s:sum(1 for r in rows if r["state"]==s) for s in allowed_states}
    if summary.get("region_count")!=len(rows):
        raise ValueError("summary region_count differs")
    if summary.get("complete")!=counts["complete"] or summary.get("partial")!=counts["partial"]:
        raise ValueError("summary visual counts differ")
    if "cannot be closed from anatomy/kinematics alone" not in str(data.get("exit_rule","")):
        raise ValueError("exit rule must block anatomy-only visual closure")
    return {"regions":len(rows),"complete":counts["complete"],"partial":counts["partial"],"missing":counts["missing"]}

def main():
    try:
        out=validate(read(VISUAL),read(MASTER),read(HUMAN))
        print("SURFACE VISUAL EVIDENCE REQUIREMENTS: PASS")
        print(json.dumps(out,indent=2))
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc))
        return 2

if __name__=="__main__":
    raise SystemExit(main())
