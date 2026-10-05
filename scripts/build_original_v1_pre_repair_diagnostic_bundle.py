#!/usr/bin/env python3
"""Build/validate a candidate-bound read-only pre-repair diagnostic bundle.

Universal diagnostics are required for every package set. Package-specific
diagnostics are included only when selected repair packages require them.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

SHOULDER_PACKAGES={"RP-NECK-TRAP-001","RP-PEC-AX-002","RP-POSTAX-003","RP-DELTOID-004"}

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def parse_packages(text):
    ids=[x.strip() for x in str(text or "").split(",") if x.strip()]
    if not ids: raise ValueError("repair packages required")
    return ids

def build(candidate,label,packages,skinning,pose_scope,pose_plan,reversibility,continuity,shoulder=None):
    candidate=Path(candidate)
    if not candidate.exists(): raise ValueError("candidate file missing")
    csha=sha(candidate)
    selected=set(packages)
    shoulder_required=bool(selected & SHOULDER_PACKAGES)
    if shoulder_required and shoulder is None:
        raise ValueError("shoulder-layer diagnostic required for selected shoulder package(s)")
    if not shoulder_required and shoulder is not None:
        raise ValueError("shoulder-layer diagnostic supplied for package set that does not require it")

    docs={
      "skinning_mode":read(skinning),
      "pose_coupling_scope":read(pose_scope),
      "pose_capture_evidence_plan":read(pose_plan),
      "motion_reversibility":read(reversibility),
      "motion_continuity":read(continuity),
    }
    paths={
      "skinning_mode":str(Path(skinning)),
      "pose_coupling_scope":str(Path(pose_scope)),
      "pose_capture_evidence_plan":str(Path(pose_plan)),
      "motion_reversibility":str(Path(reversibility)),
      "motion_continuity":str(Path(continuity)),
    }
    if shoulder_required:
        docs["shoulder_layer_diagnostic"]=read(shoulder)
        paths["shoulder_layer_diagnostic"]=str(Path(shoulder))

    mismatches={}
    for name,obj in docs.items():
        got=obj.get("candidate_sha256")
        if got!=csha: mismatches[name]=got
    if mismatches:
        raise ValueError(f"candidate SHA mismatch: expected {csha}; got {mismatches}")
    if docs["motion_reversibility"].get("overall_status") not in {"CLEAN","REVERSIBILITY_FAILURE"}:
        raise ValueError("invalid reversibility status")
    if docs["pose_coupling_scope"].get("status")!="READ_ONLY_POSE_COUPLING_SCOPE":
        raise ValueError("pose scope identity invalid")
    if docs["pose_capture_evidence_plan"].get("status")!="POSE_CAPTURE_EVIDENCE_PLAN":
        raise ValueError("pose evidence plan identity invalid")

    report={
      "schema_version":1,
      "status":"READ_ONLY_PRE_REPAIR_DIAGNOSTIC_BUNDLE",
      "production_approved":False,
      "label":label,
      "candidate":candidate.name,
      "candidate_sha256":csha,
      "repair_package_ids":packages,
      "package_specific_diagnostics":{
        "shoulder_layer_required":shoulder_required,
        "shoulder_layer_present":shoulder_required and "shoulder_layer_diagnostic" in docs,
      },
      "evidence_paths":paths,
      "evidence_sha256":{k:sha(v) for k,v in paths.items()},
      "summary":{
        "skinning_preserve_volume":[m.get("use_deform_preserve_volume") for m in docs["skinning_mode"].get("armature_modifiers",[])],
        "pose_count":len(docs["pose_coupling_scope"].get("poses",{})),
        "pose_plan_count":len(docs["pose_capture_evidence_plan"].get("poses",{})),
        "reversibility_status":docs["motion_reversibility"].get("overall_status"),
        "continuity_status":"REPORT_REQUIRES_ENGINEERING_REVIEW",
        "shoulder_layer_status":"DIAGNOSTIC_REQUIRES_ENGINEERING_REVIEW" if shoulder_required else "NOT_REQUIRED_FOR_SELECTED_PACKAGES",
      },
      "next_action":"Use ORIGINAL_V1_DEFORMATION_DIAGNOSIS_TREE.json to identify the earliest failing layer, then create a PRE-EDIT repair workspace and complete its declarations before any edit.",
      "source_saved_or_modified":False
    }
    return report

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--candidate",required=True)
    ap.add_argument("--label",required=True)
    ap.add_argument("--packages",required=True)
    ap.add_argument("--skinning",required=True)
    ap.add_argument("--pose-scope",required=True)
    ap.add_argument("--pose-plan",required=True)
    ap.add_argument("--shoulder")
    ap.add_argument("--reversibility",required=True)
    ap.add_argument("--continuity",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    try:
        report=build(
            a.candidate,a.label,parse_packages(a.packages),
            a.skinning,a.pose_scope,a.pose_plan,a.reversibility,a.continuity,a.shoulder
        )
        out=Path(a.out)
        if out.exists(): raise ValueError(f"refusing to overwrite {out}")
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
        print("PRE-REPAIR DIAGNOSTIC BUNDLE: PASS")
        print(json.dumps({
          "candidate_sha256":report["candidate_sha256"],
          "packages":report["repair_package_ids"],
          "reversibility":report["summary"]["reversibility_status"],
          "shoulder_layer_required":report["package_specific_diagnostics"]["shoulder_layer_required"],
          "out":str(out)
        },indent=2))
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2

if __name__=="__main__": raise SystemExit(main())
