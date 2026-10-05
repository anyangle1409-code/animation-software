#!/usr/bin/env python3
"""Validate a candidate-bound accepted human movement sweep."""
from __future__ import annotations
import argparse,importlib.util,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_PLAN.json"
CAL_MOD=ROOT/"scripts/validate_original_v1_human_movement_sweep_runner_calibration.py"
SHA_RE=re.compile(r"^[0-9a-f]{64}$")
PASS={"PASS","NOT_APPLICABLE"}

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def resolve(base,p):
    q=Path(p); return q if q.is_absolute() else base/q

def load(base,p):
    if not p: return None
    return read(resolve(base,p))

def bind(obj,csha,sweep=None):
    if not isinstance(obj,dict): return False,"not_object"
    got=obj.get("candidate_sha256")
    if got!=csha: return False,f"candidate_sha256={got}"
    if sweep is not None and obj.get("sweep_id")!=sweep: return False,f"sweep_id={obj.get('sweep_id')}"
    return True,"ok"

def load_calibration_validator():
    spec=importlib.util.spec_from_file_location("original_v1_sweep_calibration",CAL_MOD)
    if spec is None or spec.loader is None:
        raise ValueError("unable to load runner calibration validator")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def validate(d,base,require_pass=False):
    plan=read(PLAN)
    if d.get("schema_version")!=1: raise ValueError("schema_version must be 1")
    if d.get("production_approved") is not False: raise ValueError("sweep acceptance may not claim production approval")
    if not re.fullmatch(r"r\d+[a-z]?",str(d.get("candidate_revision","")),re.I): raise ValueError("candidate_revision invalid")
    csha=str(d.get("candidate_sha256",""))
    if not SHA_RE.fullmatch(csha): raise ValueError("candidate_sha256 invalid")
    sweep=d.get("sweep_id")
    if sweep not in (plan.get("sweeps") or {}): raise ValueError("unknown sweep_id")
    row=plan["sweeps"][sweep]

    engineering=d.get("engineering_review")
    if engineering not in {"PENDING","PASS","FAIL"}: raise ValueError("engineering_review invalid")
    if d.get("owner_review") not in {"PENDING","PASS","FAIL"}: raise ValueError("owner_review invalid")

    raw=load(base,d.get("raw_sweep_report_path"))
    if raw is None: raise ValueError("raw_sweep_report_path required")
    ok,why=bind(raw,csha)
    if not ok: raise ValueError("raw sweep report candidate mismatch: "+why)
    if sweep not in (raw.get("sweeps") or {}): raise ValueError("raw sweep report missing sweep")
    if raw.get("source_saved_or_modified") is not False: raise ValueError("raw sweep report is not read-only")

    cal=load(base,d.get("runner_calibration_record_path"))
    if engineering=="PASS" or require_pass:
        if cal is None: raise ValueError("PASS requires runner calibration record")
        try:
            calibration=load_calibration_validator().validate(cal,True)
        except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
            raise ValueError("PASS requires validated overall CALIBRATED runner record: "+str(exc)) from exc
        if calibration.get("overall_state")!="CALIBRATED":
            raise ValueError("PASS requires validated overall CALIBRATED runner record")

    vis=load(base,d.get("visual_capture_manifest_path"))
    if engineering=="PASS" or require_pass:
        if vis is None: raise ValueError("PASS requires visual capture manifest")
        ok,why=bind(vis,csha,sweep)
        if not ok: raise ValueError("visual capture manifest mismatch: "+why)
        by={x.get("label"):x for x in vis.get("samples",[])}
        for label in row.get("samples",[]):
            rec=by.get(label)
            if rec is None: raise ValueError(f"visual capture missing sample {label}")
            views=set(rec.get("views") or [])
            missing=set(row.get("cameras") or [])-views
            if missing: raise ValueError(f"{label}: visual capture missing cameras {sorted(missing)}")

    contact_required=sweep in {"grip_release","loaded_hip_hinge","ankle_plantarflexion"}
    contact=d.get("contact_review_status")
    if contact_required:
        if engineering=="PASS" or require_pass:
            if contact!="PASS": raise ValueError("contact-bearing sweep requires contact PASS")
            obj=load(base,d.get("contact_report_path"))
            if obj is None: raise ValueError("contact-bearing sweep requires contact report")
            ok,why=bind(obj,csha,sweep)
            if not ok: raise ValueError("contact report mismatch: "+why)
            if obj.get("status")!="PASS": raise ValueError("contact report status must be PASS")
    elif contact not in PASS|{"PENDING","FAIL"}:
        raise ValueError("contact_review_status invalid")

    for label,path_key,status_key in (
      ("continuity","motion_continuity_evidence_path","continuity_review_status"),
      ("reversibility","motion_reversibility_evidence_path","reversibility_review_status")
    ):
        status=d.get(status_key)
        if status not in {"PENDING","PASS","FAIL"}: raise ValueError(f"{status_key} invalid")
        if engineering=="PASS" or require_pass:
            if status!="PASS": raise ValueError(f"PASS requires {label} review PASS")
            obj=load(base,d.get(path_key))
            if obj is None: raise ValueError(f"PASS requires {label} evidence")
            ok,why=bind(obj,csha,sweep)
            if not ok: raise ValueError(f"{label} evidence mismatch: {why}")

    refs=set(d.get("human_evidence_review_refs") or [])
    if engineering=="PASS" or require_pass:
        missing=set(row.get("evidence_ids") or [])-refs
        if missing: raise ValueError(f"PASS missing human evidence review refs {sorted(missing)}")
        if d.get("visual_review_status")!="PASS": raise ValueError("PASS requires visual review PASS")
    if require_pass and engineering!="PASS": raise ValueError("engineering PASS required")
    return {"sweep_id":sweep,"candidate_sha256":csha,"engineering_review":engineering,"contact_required":contact_required}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("record"); ap.add_argument("--require-pass",action="store_true")
    a=ap.parse_args(); p=Path(a.record)
    try:
        out=validate(read(p),p.parent,a.require_pass)
        print("HUMAN MOVEMENT SWEEP ACCEPTANCE: PASS"); print(json.dumps(out,indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
