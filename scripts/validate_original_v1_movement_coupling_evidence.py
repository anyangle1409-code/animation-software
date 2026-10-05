#!/usr/bin/env python3
"""Validate candidate movement samples against automatic joint->tissue coupling triggers."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TRIGGERS=ROOT/"ORIGINAL_V1_JOINT_TISSUE_TRIGGER_MAP.json"
MASTER=ROOT/"ORIGINAL_V1_HUMAN_BODY_MASTER_PLAN.json"
MOVEMENT_REQUIREMENTS=ROOT/"ORIGINAL_V1_MOVEMENT_JOINT_FAMILY_REQUIREMENTS.json"
SHA_RE=re.compile(r"^[0-9a-f]{64}$")
VALID_STATES={"NOT_RUN","COMPLETE","BLOCKED"}

def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def derive(trigger_map,bones):
    required=set()
    matched=[]
    for row in trigger_map.get("rules",[]):
        hits=[b for b in bones if any(re.fullmatch(p,b) for p in row.get("bone_patterns",[]))]
        if hits:
            matched.append(row["id"])
            required.update(row.get("required_coupling_system_ids",[]))
    return sorted(required), sorted(matched)

def derive_joint_families(trigger_map,bones):
    families=set()
    for row in trigger_map.get("rules",[]):
        if any(any(re.fullmatch(p,b) for p in row.get("bone_patterns",[])) for b in bones):
            if row.get("joint_family"):
                families.add(row["joint_family"])
    return sorted(families)

def validate(data,triggers,master,require_complete=False,movement_requirements=None):
    if movement_requirements is None:
        movement_requirements=read(MOVEMENT_REQUIREMENTS)
    if data.get("schema_version")!=1:
        raise ValueError("schema_version must be 1")
    if data.get("production_approved") is not False:
        raise ValueError("movement coupling evidence may not claim production approval")
    rev=data.get("candidate_revision")
    sha=data.get("candidate_sha256")
    if not isinstance(rev,str) or not re.fullmatch(r"r\d+[a-z]?",rev,re.I):
        raise ValueError("candidate_revision missing/invalid")
    if not isinstance(sha,str) or not SHA_RE.fullmatch(sha):
        raise ValueError("candidate_sha256 missing/invalid")
    known_moves=set(master.get("movement_families") or [])
    samples=data.get("samples") or []
    ids=[]
    incomplete=[]
    for row in samples:
        sid=row.get("sample_id")
        if not isinstance(sid,str) or not sid:
            raise ValueError("sample_id missing")
        ids.append(sid)
        if row.get("movement_family") not in known_moves:
            raise ValueError(f"{sid}: unknown movement family")
        if row.get("state") not in VALID_STATES:
            raise ValueError(f"{sid}: invalid state")
        bones=row.get("moved_bones") or []
        if not bones:
            raise ValueError(f"{sid}: moved_bones missing")
        derived,matched=derive(triggers,bones)
        declared=sorted(row.get("required_coupling_system_ids") or [])
        if declared!=derived:
            raise ValueError(f"{sid}: required coupling systems differ from trigger-derived set; expected {derived}")
        reviewed=set(row.get("reviewed_coupling_system_ids") or [])
        missing=set(derived)-reviewed
        movement=row.get("movement_family")
        joint_families=derive_joint_families(triggers,bones)
        movement_rule=(movement_requirements.get("movements") or {}).get(movement)
        if movement_rule is None:
            raise ValueError(f"{sid}: movement joint-family requirement missing")
        required_joint=set(movement_rule.get("required_joint_families") or [])
        missing_joint=sorted(required_joint-set(joint_families))
        if row.get("state")=="COMPLETE":
            if missing:
                raise ValueError(f"{sid}: COMPLETE but missing reviewed coupling systems {sorted(missing)}")
            if not row.get("evidence_refs"):
                raise ValueError(f"{sid}: COMPLETE without evidence_refs")
            if not matched:
                raise ValueError(f"{sid}: COMPLETE but moved bones matched no trigger rules")
            if movement_rule.get("evidence_role")=="control_only":
                raise ValueError(f"{sid}: control-only movement may not satisfy active COMPLETE movement proof")
            if missing_joint:
                raise ValueError(f"{sid}: COMPLETE but moved bones miss required joint families {missing_joint}; derived {joint_families}")
        else:
            incomplete.append(sid)
    if len(ids)!=len(set(ids)):
        raise ValueError("duplicate sample_id")
    if require_complete and incomplete:
        raise ValueError(f"exit blocked: incomplete samples {incomplete}")
    return {"sample_count":len(samples),"complete":len(samples)-len(incomplete),"incomplete":incomplete}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("evidence")
    ap.add_argument("--require-complete",action="store_true")
    args=ap.parse_args()
    try:
        out=validate(read(args.evidence),read(TRIGGERS),read(MASTER),args.require_complete,read(MOVEMENT_REQUIREMENTS))
        print("MOVEMENT COUPLING EVIDENCE: PASS")
        print(json.dumps(out,indent=2))
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc))
        return 2

if __name__=="__main__":
    raise SystemExit(main())
