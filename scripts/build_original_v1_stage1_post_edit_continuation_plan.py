#!/usr/bin/env python3
"""Build exact post-edit continuation commands for one Stage-1 repair workspace.

Planning only: never edits/saves a Blend and never infers PASS.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONTACT_REQ=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_CONTACT_REQUIREMENTS.json"

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def sha_file(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for chunk in iter(lambda:f.read(1048576),b""): h.update(chunk)
    return h.hexdigest()
def dq(x): return '"' + str(x).replace('"','""') + '"'
def safe(s): return str(s).lower().replace("-","_")

def build(a):
    ws=Path(a.workspace)
    wm=read(ws/"workspace_manifest.json")
    candidate=Path(a.final_candidate)
    if not candidate.is_file(): raise ValueError("final candidate Blend not found")
    final_sha=sha_file(candidate)
    if not re.fullmatch(r"r\d+[a-z]?",a.revision,re.I): raise ValueError("revision invalid")
    if wm.get("candidate_revision")!=a.revision:
        raise ValueError("workspace candidate_revision differs")
    required=list((wm.get("validation_selection") or {}).get("sweep_only_movements_requiring_generic_runner",[]) or [])
    contact_authority=set((read(CONTACT_REQ).get("sweeps") or {}).keys())
    contact_sweeps=[x for x in required if x in contact_authority]
    sweep_csv=",".join(required)
    contact_csv=",".join(contact_sweeps)
    raw_dir=Path("ORIGINAL_V1_WORK/candidates/repair_checks/human_movement_sweeps")/(a.label+"_post_sweeps")
    raw=raw_dir/"human_movement_sweeps.json"
    visual_dir=Path("ORIGINAL_V1_WORK/candidates/repair_checks/human_movement_sweep_visuals")/(a.label+"_post_visuals")
    contact_dir=Path("ORIGINAL_V1_WORK/candidates/repair_checks/human_movement_sweep_contact")/(a.label+"_post_contact")
    cal=Path(a.calibration_record) if a.calibration_record else None

    finalized=(ws/"workspace_finalization_manifest.json").is_file()
    if finalized:
        fm=read(ws/"workspace_finalization_manifest.json")
        if fm.get("final_candidate_sha256")!=final_sha:
            raise ValueError("workspace already finalized to different candidate SHA")

    commands=[]
    if not finalized:
        commands.append({
          "phase":"finalize_workspace",
          "command":"RUN_ORIGINAL_V1_FINALIZE_REPAIR_WORKSPACE.bat "+dq(ws)+" "+dq(candidate),
          "blocking":True
        })
    commands.append({
      "phase":"post_repair_core_validation",
      "command":"RUN_ORIGINAL_V1_POST_REPAIR_VALIDATION_BUNDLE.bat "+dq(a.revision)+" "+dq(a.prior)+" "+dq(ws)+" "+dq(a.label),
      "blocking":True
    })

    if required:
        if cal is None:
            raise ValueError("required sweep-only movements need --calibration-record")
        if not cal.is_file():
            raise ValueError("calibration record not found")
        cal_obj=read(cal)
        if cal_obj.get("runner_id")!="generic_human_movement_sweep_v1":
            raise ValueError("calibration runner identity differs")
        if cal_obj.get("overall_state")!="CALIBRATED" or cal_obj.get("engineering_review")!="PASS":
            raise ValueError("required sweep-only movements need CALIBRATED runner record with engineering PASS")
        commands.append({
          "phase":"post_repair_required_sweeps",
          "command":"RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEPS.bat "+dq(candidate)+" "+dq(a.label+"_post_sweeps")+" "+dq(sweep_csv),
          "blocking":True
        })
        commands.append({
          "phase":"post_repair_sweep_visuals",
          "command":"RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_VISUALS.bat "+dq(candidate)+" "+dq(a.revision)+" "+dq(a.label+"_post_visuals")+" "+dq(sweep_csv),
          "blocking":True
        })
        if contact_sweeps:
            commands.append({
              "phase":"post_repair_sweep_contact_raw",
              "command":"RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_CONTACT_RAW.bat "+dq(candidate)+" "+dq(a.revision)+" "+dq(a.label+"_post_contact")+" "+dq(contact_csv),
              "blocking":True
            })
        collect="RUN_ORIGINAL_V1_COLLECT_WORKSPACE_SWEEP_EVIDENCE.bat "+dq(ws)+" "+dq(raw)+" "+dq(visual_dir)+" "+dq(cal)
        if contact_sweeps:
            collect+=" "+dq(contact_dir)
        commands.append({"phase":"collect_sweep_evidence","command":collect,"blocking":True})
        for sid in required:
            motion=ws/f"human_movement_sweep_motion_{safe(sid)}_final.json"
            commands.append({
              "phase":"build_sweep_motion_review:"+sid,
              "command":"RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_MOTION_REVIEW.bat "+dq(raw)+" "+dq(sid)+" "+dq(a.revision)+" "+dq(motion),
              "blocking":True
            })
        commands.append({
          "phase":"sweep_engineering_review_gate",
          "command":"Review/fill every generated sweep visual, contact (where required), motion and acceptance record; validate each acceptance with --require-pass before unified comparison.",
          "blocking":True,
          "review_gate":True
        })

    commands.append({
      "phase":"complete_candidate_records",
      "command":"Complete/validate repair execution records, weights-only evidence, coupling evidence, movement-coupling evidence, surface visual review, regression/contact/change reviews and candidate issue-ledger dispositions against the FINAL SHA.",
      "blocking":True,
      "review_gate":True
    })
    comparison_manifest=ws/"candidate_comparison_manifest_post_repair.json"
    commands.append({
      "phase":"unified_candidate_comparison",
      "command":"RUN_ORIGINAL_V1_CANDIDATE_COMPARISON.bat "+dq(comparison_manifest)+" "+dq(ws/"candidate_comparison_report.json"),
      "blocking":True
    })
    commands.append({
      "phase":"progress_update",
      "command":"Only after the comparison is engineering-clear eligible: update Stage-1 progress/issue closure evidence; owner review remains separate.",
      "blocking":True,
      "review_gate":True
    })

    return {
      "schema_version":1,
      "status":"STAGE1_POST_EDIT_CONTINUATION_PLAN",
      "production_approved":False,
      "generated_without_blender":True,
      "workspace":str(ws),
      "candidate_revision":a.revision,
      "final_candidate":{"path":str(candidate),"sha256":final_sha},
      "prior_revision":a.prior,
      "label":a.label,
      "repair_package_ids":wm.get("repair_package_ids",[]),
      "required_sweep_only_movements":required,
      "contact_bearing_required_sweeps":contact_sweeps,
      "calibration_record":str(cal) if cal else None,
      "workspace_already_finalized":finalized,
      "commands":commands,
      "stop_conditions":[
        "workspace final SHA differs from actual candidate",
        "post-repair core validation fails",
        "required calibrated sweep record missing",
        "required sweep raw/visual/contact evidence missing",
        "any sweep acceptance remains PENDING/FAIL",
        "repair execution exceeds declaration scope",
        "weights-only/coupling/movement/visual/regression/contact/change evidence incomplete",
        "new Critical/High defect introduced",
        "unified comparison remains blocked"
      ],
      "note":"Planning/orchestration only. It never infers engineering PASS, owner acceptance or production approval."
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--workspace",required=True)
    ap.add_argument("--final-candidate",required=True)
    ap.add_argument("--revision",required=True)
    ap.add_argument("--prior",required=True)
    ap.add_argument("--label",required=True)
    ap.add_argument("--calibration-record")
    ap.add_argument("--out-dir",required=True)
    a=ap.parse_args()
    try:
        d=build(a)
        out=Path(a.out_dir)
        if out.exists() and any(out.iterdir()): raise ValueError("output directory is not empty")
        out.mkdir(parents=True,exist_ok=True)
        (out/"post_edit_continuation_plan.json").write_text(json.dumps(d,indent=2)+"\n",encoding="utf-8")
        lines=[
          "# ORIGINAL v1 Stage 1 post-edit continuation","",
          "Candidate: "+d["candidate_revision"]+" — "+d["final_candidate"]["sha256"],
          "Packages: "+(", ".join(d["repair_package_ids"]) or "none"),
          "Required sweep-only movements: "+(", ".join(d["required_sweep_only_movements"]) or "none"),
          "","## Run order",""
        ]
        for i,row in enumerate(d["commands"],1):
            lines.append(f"{i}. {row['phase']}")
            lines.append("   "+row["command"])
            if row.get("review_gate"): lines.append("   REVIEW GATE — do not skip")
        (out/"post_edit_continuation_plan.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
        print("STAGE1 POST-EDIT CONTINUATION PLAN: READY")
        print(json.dumps({"revision":d["candidate_revision"],"sha256":d["final_candidate"]["sha256"],"sweeps":d["required_sweep_only_movements"],"commands":len(d["commands"])},indent=2))
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP - "+str(exc)); return 2

if __name__=="__main__": raise SystemExit(main())
