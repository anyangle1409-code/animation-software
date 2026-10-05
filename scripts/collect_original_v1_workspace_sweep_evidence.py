#!/usr/bin/env python3
"""Collect raw generic-sweep evidence into one finalized repair workspace.

Copies raw motion report, calibration record, rendered images/manifests and raw
contact measurements into the workspace. It pre-fills pointers in the generated
review/acceptance records but NEVER sets engineering/owner PASS.
"""
from __future__ import annotations
import argparse,hashlib,json,os,shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONTACT_REQ=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_CONTACT_REQUIREMENTS.json"

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def write(p,d): p.write_text(json.dumps(d,indent=2)+"\n",encoding="utf-8")
def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rel(p,base): return os.path.relpath(str(Path(p)),str(Path(base))).replace("\\","/")
def stem(s): return s.lower().replace("-","_")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--workspace",required=True)
    ap.add_argument("--raw-sweep-report",required=True)
    ap.add_argument("--visual-dir",required=True)
    ap.add_argument("--calibration-record",required=True)
    ap.add_argument("--contact-dir")
    a=ap.parse_args()
    try:
        ws=Path(a.workspace)
        fm=read(ws/"workspace_finalization_manifest.json")
        wm=read(ws/"workspace_manifest.json")
        final=fm["final_candidate_sha256"]
        required=list(wm.get("validation_selection",{}).get("sweep_only_movements_requiring_generic_runner",[]) or [])
        if not required:
            print("WORKSPACE SWEEP EVIDENCE: NO SWEEP-ONLY MOVEMENTS REQUIRED"); return 0

        raw_path=Path(a.raw_sweep_report)
        if not raw_path.is_file(): raise ValueError("raw sweep report missing")
        raw=read(raw_path)
        if raw.get("candidate_sha256")!=final: raise ValueError("raw sweep report candidate SHA differs from workspace FINAL SHA")
        missing=sorted(set(required)-set(raw.get("sweeps",{})))
        if missing: raise ValueError(f"raw sweep report missing required sweeps {missing}")

        cal_path=Path(a.calibration_record)
        if not cal_path.is_file(): raise ValueError("runner calibration record missing")
        cal=read(cal_path)
        if cal.get("runner_id")!="generic_human_movement_sweep_v1": raise ValueError("calibration runner identity differs")

        visual_dir=Path(a.visual_dir)
        if not visual_dir.is_dir(): raise ValueError("visual capture directory missing")
        contact_dir=Path(a.contact_dir) if a.contact_dir else None
        contact_authority=read(CONTACT_REQ).get("sweeps",{})

        dest=ws/"sweep_evidence_raw"
        if dest.exists(): raise ValueError("workspace sweep_evidence_raw already exists")
        (dest/"visual").mkdir(parents=True)
        (dest/"contact").mkdir(parents=True)

        raw_dst=dest/"human_movement_sweeps.json"; shutil.copy2(raw_path,raw_dst)
        cal_dst=dest/"runner_calibration.json"; shutil.copy2(cal_path,cal_dst)

        visual_records={}
        contact_records={}
        acceptance_records={}
        copied_images=[]

        for sid in required:
            sstem=stem(sid)
            source_manifest=visual_dir/f"human_movement_sweep_visual_{sid}.json"
            if not source_manifest.is_file(): raise ValueError(f"visual manifest missing for {sid}")
            vis=read(source_manifest)
            if vis.get("candidate_sha256")!=final or vis.get("sweep_id")!=sid:
                raise ValueError(f"{sid}: visual manifest identity differs")
            for sample in vis.get("samples",[]):
                for view in sample.get("views",[]):
                    src_img=visual_dir/view["path"]
                    if not src_img.is_file(): raise ValueError(f"{sid}: visual image missing {src_img}")
                    dst_img=dest/"visual"/src_img.name
                    if dst_img.exists(): raise ValueError(f"duplicate visual image name {src_img.name}")
                    shutil.copy2(src_img,dst_img)
                    if digest(dst_img)!=view.get("sha256"): raise ValueError(f"{sid}: copied image SHA differs")
                    view["path"]=rel(dst_img,ws)
                    copied_images.append(rel(dst_img,ws))
            target_visual=ws/f"human_movement_sweep_visual_{sstem}_final.json"
            existing=read(target_visual)
            if existing.get("engineering_review")!="PENDING" or any(x.get("views") for x in existing.get("samples",[])):
                raise ValueError(f"{sid}: target visual record is no longer an empty PENDING scaffold")
            write(target_visual,vis)
            visual_records[sid]=target_visual.name

            target_contact=None
            if sid in contact_authority:
                if contact_dir is None: raise ValueError(f"{sid}: contact-bearing sweep requires contact directory")
                raw_contact=contact_dir/f"human_movement_sweep_contact_raw_{sid}.json"
                if not raw_contact.is_file(): raise ValueError(f"{sid}: raw contact file missing")
                rc=read(raw_contact)
                if rc.get("candidate_sha256")!=final or rc.get("sweep_id")!=sid:
                    raise ValueError(f"{sid}: raw contact identity differs")
                raw_contact_dst=dest/"contact"/raw_contact.name; shutil.copy2(raw_contact,raw_contact_dst)
                target_contact=ws/f"human_movement_sweep_contact_{sstem}_final.json"
                cr=read(target_contact)
                if cr.get("engineering_review")!="PENDING": raise ValueError(f"{sid}: contact record already reviewed")
                cr["raw_contact_evidence_refs"]=[{
                  "path":rel(raw_contact_dst,ws),
                  "sha256":digest(raw_contact_dst),
                  "candidate_sha256":final
                }]
                raw_by={x["label"]:x for x in rc.get("samples",[])}
                for i,row in enumerate(cr.get("samples",[])):
                    label=row["label"]
                    if label not in raw_by: raise ValueError(f"{sid}/{label}: raw contact sample missing")
                    for domain,rec in row.get("domains",{}).items():
                        if domain in raw_by[label].get("domains",{}):
                            rec["raw_measurement_ref"]=rel(raw_contact_dst,ws)+f"#samples/{i}/domains/{domain}"
                            rec["evidence_note"]="Candidate-bound raw geometry captured automatically; engineering classification remains UNCLASSIFIED pending review."
                write(target_contact,cr)
                contact_records[sid]=target_contact.name

            acc_path=ws/f"human_movement_sweep_acceptance_{sstem}_final.json"
            acc=read(acc_path)
            if acc.get("engineering_review")!="PENDING": raise ValueError(f"{sid}: acceptance record already reviewed")
            acc["raw_sweep_report_path"]=rel(raw_dst,ws)
            acc["runner_calibration_record_path"]=rel(cal_dst,ws)
            acc["visual_capture_manifest_path"]=visual_records[sid]
            acc["contact_report_path"]=target_contact.name if target_contact else None
            motion_name=f"human_movement_sweep_motion_{sstem}_final.json"
            acc["motion_continuity_evidence_path"]=motion_name
            acc["motion_reversibility_evidence_path"]=motion_name
            write(acc_path,acc)
            acceptance_records[sid]=acc_path.name

        index={
          "schema_version":1,
          "status":"WORKSPACE_SWEEP_EVIDENCE_COLLECTED",
          "production_approved":False,
          "candidate_revision":fm["candidate_revision"],
          "candidate_sha256":final,
          "required_sweeps":required,
          "raw_sweep_report":{"path":rel(raw_dst,ws),"sha256":digest(raw_dst)},
          "runner_calibration_record":{"path":rel(cal_dst,ws),"sha256":digest(cal_dst),"overall_state":cal.get("overall_state")},
          "visual_records":visual_records,
          "contact_records":contact_records,
          "acceptance_records":acceptance_records,
          "copied_visual_images":copied_images,
          "engineering_statuses":"PENDING",
          "note":"Collection/pointer population only. No visual/contact/motion/sweep acceptance PASS is inferred."
        }
        write(ws/"workspace_sweep_evidence_index.json",index)
        print("WORKSPACE SWEEP EVIDENCE: COLLECTED")
        print(json.dumps({"candidate_sha256":final,"sweeps":required,"images":len(copied_images),"contact_sweeps":sorted(contact_records)},indent=2))
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError,shutil.Error) as exc:
        print("STOP - "+str(exc)); return 2

if __name__=="__main__": raise SystemExit(main())
