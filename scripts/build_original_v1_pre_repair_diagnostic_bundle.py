#!/usr/bin/env python3
"""Build/validate a candidate-bound read-only pre-repair diagnostic bundle."""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path
SHA_RE=re.compile(r"^[0-9a-f]{64}$")

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--candidate",required=True)
    ap.add_argument("--label",required=True)
    ap.add_argument("--skinning",required=True)
    ap.add_argument("--pose-scope",required=True)
    ap.add_argument("--pose-plan",required=True)
    ap.add_argument("--shoulder",required=True)
    ap.add_argument("--reversibility",required=True)
    ap.add_argument("--continuity",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    try:
        candidate=Path(a.candidate)
        if not candidate.exists(): raise ValueError("candidate file missing")
        csha=sha(candidate)
        docs={
          "skinning_mode":read(a.skinning),
          "pose_coupling_scope":read(a.pose_scope),
          "pose_capture_evidence_plan":read(a.pose_plan),
          "shoulder_layer_diagnostic":read(a.shoulder),
          "motion_reversibility":read(a.reversibility),
          "motion_continuity":read(a.continuity),
        }
        candidate_fields={
          "skinning_mode":"candidate_sha256",
          "pose_coupling_scope":"candidate_sha256",
          "pose_capture_evidence_plan":"candidate_sha256",
          "shoulder_layer_diagnostic":"candidate_sha256",
          "motion_reversibility":"candidate_sha256",
          "motion_continuity":"candidate_sha256",
        }
        mismatches={}
        for name,obj in docs.items():
            got=obj.get(candidate_fields[name])
            if got!=csha: mismatches[name]=got
        if mismatches: raise ValueError(f"candidate SHA mismatch: expected {csha}; got {mismatches}")
        if docs["motion_reversibility"].get("overall_status") not in {"CLEAN","REVERSIBILITY_FAILURE"}:
            raise ValueError("invalid reversibility status")
        if docs["pose_coupling_scope"].get("status")!="READ_ONLY_POSE_COUPLING_SCOPE":
            raise ValueError("pose scope identity invalid")
        if docs["pose_capture_evidence_plan"].get("status")!="POSE_CAPTURE_EVIDENCE_PLAN":
            raise ValueError("pose evidence plan identity invalid")
        paths={
          "skinning_mode":str(Path(a.skinning)),
          "pose_coupling_scope":str(Path(a.pose_scope)),
          "pose_capture_evidence_plan":str(Path(a.pose_plan)),
          "shoulder_layer_diagnostic":str(Path(a.shoulder)),
          "motion_reversibility":str(Path(a.reversibility)),
          "motion_continuity":str(Path(a.continuity)),
        }
        report={
          "schema_version":1,
          "status":"READ_ONLY_PRE_REPAIR_DIAGNOSTIC_BUNDLE",
          "production_approved":False,
          "label":a.label,
          "candidate":candidate.name,
          "candidate_sha256":csha,
          "evidence_paths":paths,
          "evidence_sha256":{k:sha(v) for k,v in paths.items()},
          "summary":{
            "skinning_preserve_volume":[m.get("use_deform_preserve_volume") for m in docs["skinning_mode"].get("armature_modifiers",[])],
            "pose_count":len(docs["pose_coupling_scope"].get("poses",{})),
            "pose_plan_count":len(docs["pose_capture_evidence_plan"].get("poses",{})),
            "reversibility_status":docs["motion_reversibility"].get("overall_status"),
            "continuity_status":"REPORT_REQUIRES_ENGINEERING_REVIEW",
            "shoulder_layer_status":"DIAGNOSTIC_REQUIRES_ENGINEERING_REVIEW"
          },
          "next_action":"Use ORIGINAL_V1_DEFORMATION_DIAGNOSIS_TREE.json to identify the earliest failing layer, then create a candidate-specific repair declaration before any edit.",
          "source_saved_or_modified":False
        }
        out=Path(a.out)
        if out.exists(): raise ValueError(f"refusing to overwrite {out}")
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
        print("PRE-REPAIR DIAGNOSTIC BUNDLE: PASS")
        print(json.dumps({"candidate_sha256":csha,"reversibility":report["summary"]["reversibility_status"],"out":str(out)},indent=2))
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2

if __name__=="__main__": raise SystemExit(main())
