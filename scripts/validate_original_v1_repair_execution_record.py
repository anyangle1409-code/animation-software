#!/usr/bin/env python3
"""Validate post-edit ORIGINAL-v1 repair execution provenance."""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path

SHA_RE=re.compile(r"^[0-9a-f]{64}$")

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def validate(rec,base):
    if rec.get("schema_version")!=1: raise ValueError("schema_version must be 1")
    if rec.get("production_approved") is not False: raise ValueError("execution record may not claim production approval")
    if not re.fullmatch(r"r\d+[a-z]?",str(rec.get("candidate_revision","")),re.I): raise ValueError("candidate_revision invalid")
    for key in ("repair_declaration_sha256","pre_edit_candidate_sha256","final_candidate_sha256"):
        if not SHA_RE.fullmatch(str(rec.get(key,""))): raise ValueError(f"{key} invalid")
    if rec["pre_edit_candidate_sha256"]==rec["final_candidate_sha256"]:
        raise ValueError("final candidate SHA must differ from pre-edit SHA for an executed repair")

    dp=Path(rec.get("repair_declaration_path") or "")
    dp=dp if dp.is_absolute() else base/dp
    if not dp.exists(): raise ValueError("repair declaration path missing")
    raw=dp.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=rec["repair_declaration_sha256"]:
        raise ValueError("repair declaration hash mismatch")
    dec=json.loads(raw.decode("utf-8"))
    if dec.get("candidate_revision")!=rec.get("candidate_revision"): raise ValueError("candidate revision differs from declaration")
    pre=dec.get("pre_edit_candidate_sha256") or dec.get("candidate_sha256")
    if pre!=rec["pre_edit_candidate_sha256"]: raise ValueError("pre-edit candidate SHA differs from declaration")
    if dec.get("repair_package_id")!=rec.get("repair_package_id"): raise ValueError("repair package differs from declaration")
    if dec.get("coupling_system_id")!=rec.get("coupling_system_id"): raise ValueError("coupling system differs from declaration")
    if dec.get("side")!=rec.get("side"): raise ValueError("side differs from declaration")

    ops=rec.get("executed_operations") or []
    if not ops: raise ValueError("executed_operations required")
    forbidden=set(dec.get("forbidden_operations") or [])
    bad_ops=sorted(set(ops)&forbidden)
    if bad_ops: raise ValueError(f"forbidden executed operations {bad_ops}")
    allowed_ops=set(dec.get("allowed_operations") or [])
    undeclared_ops=sorted(set(ops)-allowed_ops)
    if undeclared_ops: raise ValueError(f"undeclared executed operations {undeclared_ops}")

    edited=set(rec.get("edited_vertex_ids") or [])
    if not edited: raise ValueError("edited_vertex_ids required")
    if any(not isinstance(x,int) or x<0 for x in edited): raise ValueError("edited_vertex_ids invalid")
    allowed=set((dec.get("zones") or {}).get("allowed_edit_vertex_ids") or [])
    protected=set((dec.get("zones") or {}).get("protected_neighbor_vertex_ids") or [])
    if not edited.issubset(allowed): raise ValueError("edited vertices exceed declaration allowed_edit_vertex_ids")
    if edited & protected: raise ValueError("edited vertices overlap protected neighbours")

    edited_bones=set(rec.get("edited_bone_groups") or [])
    if not edited_bones: raise ValueError("edited_bone_groups required")
    allowed_bones=set(dec.get("allowed_bones") or [])
    if not edited_bones.issubset(allowed_bones):
        raise ValueError("edited bone groups exceed declaration allowed_bones")

    if not rec.get("evidence_refs"): raise ValueError("evidence_refs required")
    for key in ("change_audit_path","regression_report_path"):
        if not rec.get(key): raise ValueError(f"{key} required")
    return {
      "candidate_revision":rec["candidate_revision"],
      "repair_package_id":rec.get("repair_package_id"),
      "coupling_system_id":rec.get("coupling_system_id"),
      "edited_vertex_count":len(edited),
      "edited_bone_group_count":len(edited_bones),
      "status":"PASS"
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("record")
    args=ap.parse_args(); p=Path(args.record)
    try:
        out=validate(read(p),p.parent)
        print("REPAIR EXECUTION RECORD: PASS")
        print(json.dumps(out,indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2

if __name__=="__main__":
    raise SystemExit(main())
