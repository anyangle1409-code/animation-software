#!/usr/bin/env python3
"""Create per-sweep review/acceptance workspaces from candidate-bound evidence.

Inputs:
- raw generic sweep report (one report can contain many sweeps)
- candidate revision
- calibrated/in-review runner calibration record path
- visual capture directory
- raw contact directory (required only for contact-bearing sweeps)
- fresh output directory

Outputs per sweep:
- motion review scaffold
- contact classification scaffold when applicable
- acceptance record scaffold
- workspace manifest

No PASS/CLEAR is inferred.
"""
from __future__ import annotations
import argparse,copy,hashlib,importlib.util,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_PLAN.json"
ACCEPT_TEMPLATE=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_ACCEPTANCE_TEMPLATE.json"
MOTION_BUILDER=ROOT/"scripts/build_original_v1_human_movement_sweep_motion_review.py"
CONTACT_BUILDER=ROOT/"scripts/build_original_v1_human_movement_sweep_contact_review.py"
RAW_VALIDATOR=ROOT/"scripts/validate_original_v1_human_movement_sweep_report.py"
VISUAL_VALIDATOR=ROOT/"scripts/validate_original_v1_human_movement_sweep_visual_capture.py"
CONTACT_RAW_VALIDATOR=ROOT/"scripts/validate_original_v1_human_movement_sweep_contact_raw.py"
CAL_VALIDATOR=ROOT/"scripts/validate_original_v1_human_movement_sweep_runner_calibration.py"
CONTACT_BEARING={"grip_release","loaded_hip_hinge","ankle_plantarflexion"}

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def module(path,name):
    sp=importlib.util.spec_from_file_location(name,path)
    if sp is None or sp.loader is None: raise ValueError(f"unable to load {name}")
    m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def build(raw_path,revision,calibration_path,visual_dir,contact_dir,out_dir,sweeps=None):
    raw_path=Path(raw_path); calibration_path=Path(calibration_path)
    visual_dir=Path(visual_dir); contact_dir=Path(contact_dir) if contact_dir else None; out_dir=Path(out_dir)
    raw=read(raw_path)
    rv=module(RAW_VALIDATOR,"raw_sweep_validator"); rv.validate(raw,rv.read(rv.SPEC))
    cal=read(calibration_path)
    cv=module(CAL_VALIDATOR,"calibration_validator"); cv.validate(cal,False)
    plan=read(PLAN)
    selected=list(raw.get("sweeps",{})) if not sweeps else sweeps
    unknown=sorted(set(selected)-set(raw.get("sweeps",{})))
    if unknown: raise ValueError(f"requested sweeps absent from raw report {unknown}")
    if out_dir.exists(): raise ValueError(f"refusing to reuse output directory {out_dir}")
    out_dir.mkdir(parents=True)

    motion_builder=module(MOTION_BUILDER,"motion_builder")
    contact_builder=module(CONTACT_BUILDER,"contact_builder")
    visual_validator=module(VISUAL_VALIDATOR,"visual_validator")
    contact_raw_validator=module(CONTACT_RAW_VALIDATOR,"contact_raw_validator")
    accept_template=read(ACCEPT_TEMPLATE)
    manifest={
      "schema_version":1,
      "status":"HUMAN_MOVEMENT_SWEEP_REVIEW_WORKSPACE",
      "production_approved":False,
      "candidate_revision":revision,
      "candidate_sha256":raw["candidate_sha256"],
      "raw_sweep_report_path":str(raw_path),
      "raw_sweep_report_sha256":sha(raw_path),
      "runner_calibration_record_path":str(calibration_path),
      "runner_calibration_record_sha256":sha(calibration_path),
      "sweeps":{},
      "engineering_review":"PENDING",
      "owner_review":"PENDING"
    }

    for sweep in selected:
        if sweep not in plan["sweeps"]: raise ValueError(f"unknown sweep {sweep}")
        sd=out_dir/sweep; sd.mkdir()
        visual_path=visual_dir/f"human_movement_sweep_visual_{sweep}.json"
        if not visual_path.is_file(): raise ValueError(f"{sweep}: visual manifest missing {visual_path}")
        visual=read(visual_path)
        visual_validator.validate(visual,visual_path.parent,False)
        if visual.get("candidate_sha256")!=raw["candidate_sha256"]:
            raise ValueError(f"{sweep}: visual candidate differs from raw sweep report")

        motion=motion_builder.build(raw_path,sweep,revision)
        motion_path=sd/"motion_review.json"
        motion_path.write_text(json.dumps(motion,indent=2)+"\n",encoding="utf-8")

        contact_review_path=None
        raw_contact_path=None
        if sweep in CONTACT_BEARING:
            if contact_dir is None: raise ValueError(f"{sweep}: contact directory required")
            raw_contact_path=contact_dir/f"human_movement_sweep_contact_raw_{sweep}.json"
            if not raw_contact_path.is_file(): raise ValueError(f"{sweep}: raw contact report missing {raw_contact_path}")
            raw_contact=read(raw_contact_path); contact_raw_validator.validate(raw_contact)
            if raw_contact.get("candidate_sha256")!=raw["candidate_sha256"]:
                raise ValueError(f"{sweep}: raw contact candidate differs")
            contact_review_path=sd/"contact_review.json"
            contact_builder.build(raw_contact_path,contact_review_path)

        acc=copy.deepcopy(accept_template)
        acc["status"]="HUMAN_MOVEMENT_SWEEP_ACCEPTANCE"
        acc["candidate_revision"]=revision
        acc["candidate_sha256"]=raw["candidate_sha256"]
        acc["sweep_id"]=sweep
        acc["raw_sweep_report_path"]=str(raw_path)
        acc["runner_calibration_record_path"]=str(calibration_path)
        acc["visual_capture_manifest_path"]=str(visual_path)
        acc["contact_report_path"]=str(contact_review_path) if contact_review_path else None
        acc["motion_continuity_evidence_path"]=str(motion_path)
        acc["motion_reversibility_evidence_path"]=str(motion_path)
        acc["required_human_evidence_ids"]=list(plan["sweeps"][sweep].get("evidence_ids") or [])
        acc["human_evidence_review_refs"]=[]
        acc["continuity_review_status"]="PENDING"
        acc["reversibility_review_status"]="PENDING"
        acc["visual_review_status"]="PENDING"
        acc["contact_review_status"]="PENDING" if sweep in CONTACT_BEARING else "NOT_APPLICABLE"
        acc["engineering_review"]="PENDING"; acc["owner_review"]="PENDING"
        acceptance_path=sd/"acceptance.json"
        acceptance_path.write_text(json.dumps(acc,indent=2)+"\n",encoding="utf-8")

        manifest["sweeps"][sweep]={
          "visual_capture_manifest_path":str(visual_path),
          "motion_review_path":str(motion_path),
          "raw_contact_path":str(raw_contact_path) if raw_contact_path else None,
          "contact_review_path":str(contact_review_path) if contact_review_path else None,
          "acceptance_path":str(acceptance_path),
          "required_human_evidence_ids":acc["required_human_evidence_ids"],
          "state":"REVIEW_PENDING"
        }

    (out_dir/"workspace_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    return manifest

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("raw_report")
    ap.add_argument("candidate_revision")
    ap.add_argument("calibration_record")
    ap.add_argument("visual_dir")
    ap.add_argument("contact_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--sweeps")
    a=ap.parse_args()
    try:
        sweeps=[x.strip() for x in a.sweeps.split(",") if x.strip()] if a.sweeps else None
        contact_dir=None if a.contact_dir in {"-","NONE","none"} else a.contact_dir
        d=build(a.raw_report,a.candidate_revision,a.calibration_record,a.visual_dir,contact_dir,a.out_dir,sweeps)
        print("HUMAN SWEEP REVIEW WORKSPACE: BUILT")
        print(json.dumps({"candidate_revision":d["candidate_revision"],"candidate_sha256":d["candidate_sha256"],"sweeps":list(d["sweeps"])},indent=2))
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
