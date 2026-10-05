#!/usr/bin/env python3
"""Finalize one reviewed human-movement sweep acceptance record.

This script derives review-status fields from already-reviewed referenced
evidence, sets engineering_review PASS, and validates the complete acceptance
contract before writing a new file. It never changes owner_review or production
approval.
"""
from __future__ import annotations
import argparse,copy,importlib.util,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VALIDATOR=ROOT/"scripts/validate_original_v1_human_movement_sweep_acceptance.py"
CONTACT_BEARING={"grip_release","loaded_hip_hinge","ankle_plantarflexion"}

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def resolve(base,p):
    q=Path(p); return q if q.is_absolute() else base/q

def load_validator():
    sp=importlib.util.spec_from_file_location("sweep_acceptance_validator",VALIDATOR)
    if sp is None or sp.loader is None: raise ValueError("unable to load sweep acceptance validator")
    m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m

def finalize(record,base):
    if record.get("status")!="HUMAN_MOVEMENT_SWEEP_ACCEPTANCE":
        raise ValueError("input must be a human movement sweep acceptance record")
    if record.get("production_approved") is not False:
        raise ValueError("acceptance may not claim production approval")
    sweep=record.get("sweep_id")
    if not sweep: raise ValueError("sweep_id missing")
    out=copy.deepcopy(record)

    required=set(out.get("required_human_evidence_ids") or [])
    refs=set(out.get("human_evidence_review_refs") or [])
    missing=sorted(required-refs)
    if missing:
        raise ValueError(f"missing required human-evidence review refs {missing}")

    visual=read(resolve(base,out.get("visual_capture_manifest_path")))
    if visual.get("engineering_review")!="PASS":
        raise ValueError("visual capture engineering review PASS required")
    out["visual_review_status"]="PASS"

    motion_path=out.get("motion_continuity_evidence_path")
    if not motion_path or motion_path!=out.get("motion_reversibility_evidence_path"):
        raise ValueError("one shared motion-review record is required for continuity/reversibility")
    motion=read(resolve(base,motion_path))
    if motion.get("continuity_review")!="PASS":
        raise ValueError("motion continuity review PASS required")
    if motion.get("reversibility_review")!="PASS":
        raise ValueError("motion reversibility review PASS required")
    if motion.get("engineering_review")!="PASS":
        raise ValueError("motion engineering review PASS required")
    out["continuity_review_status"]="PASS"
    out["reversibility_review_status"]="PASS"

    if sweep in CONTACT_BEARING:
        contact_path=out.get("contact_report_path")
        if not contact_path: raise ValueError("contact-bearing sweep requires contact report")
        contact=read(resolve(base,contact_path))
        if contact.get("engineering_review")!="PASS":
            raise ValueError("contact engineering review PASS required")
        out["contact_review_status"]="PASS"
    else:
        out["contact_review_status"]="NOT_APPLICABLE"

    out["engineering_review"]="PASS"
    out["owner_review"]="PENDING"

    validator=load_validator()
    validator.validate(out,base,True)
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("reviewed_acceptance")
    ap.add_argument("out")
    a=ap.parse_args()
    try:
        src=Path(a.reviewed_acceptance); dst=Path(a.out)
        if not src.is_file(): raise ValueError("reviewed acceptance record not found")
        if dst.exists(): raise ValueError(f"refusing to overwrite {dst}")
        d=finalize(read(src),src.parent)
        dst.parent.mkdir(parents=True,exist_ok=True)
        dst.write_text(json.dumps(d,indent=2)+"\n",encoding="utf-8")
        print("HUMAN MOVEMENT SWEEP ACCEPTANCE: ENGINEERING PASS")
        print(json.dumps({
          "candidate_revision":d["candidate_revision"],
          "candidate_sha256":d["candidate_sha256"],
          "sweep_id":d["sweep_id"],
          "engineering_review":d["engineering_review"],
          "owner_review":d["owner_review"]
        },indent=2))
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2

if __name__=="__main__": raise SystemExit(main())
