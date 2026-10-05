#!/usr/bin/env python3
"""Create a fresh candidate-specific anatomical repair declaration from a repair package.

This tool does NOT choose vertices or weights. It pre-fills the evidence-backed
anatomical contract so Blender work only has to declare the actual local vertex
zones/bone groups before editing.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PACKAGES=ROOT/"ORIGINAL_V1_ANATOMICAL_REPAIR_PACKAGES.json"
COUPLING=ROOT/"ORIGINAL_V1_ANATOMICAL_COUPLING_MAP.json"
DEFECTS=ROOT/"ORIGINAL_V1_DEFECT_COUPLING_MAP.json"
TEMPLATE=ROOT/"ORIGINAL_V1_COUPLING_ZONE_DECLARATION_TEMPLATE.json"
SHA_RE=re.compile(r"^[0-9a-f]{64}$")

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--package",required=True,dest="package_id")
    ap.add_argument("--candidate",required=True)
    ap.add_argument("--sha256",required=True)
    ap.add_argument("--side",required=True,choices=["l","r","bilateral","midline"])
    ap.add_argument("--source-branch",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    try:
        if not re.fullmatch(r"r\d+[a-z]?",a.candidate,re.I): raise ValueError("candidate revision invalid")
        if not SHA_RE.fullmatch(a.sha256): raise ValueError("candidate sha256 invalid")
        packages=read(PACKAGES); coupling=read(COUPLING); defects=read(DEFECTS); t=read(TEMPLATE)
        pkg=next((x for x in packages["packages"] if x["id"]==a.package_id),None)
        if pkg is None: raise ValueError("unknown repair package")
        cid=pkg["coupling_system_id"]
        cp=next(x for x in coupling["coupling_systems"] if x["id"]==cid)
        linked=[x["issue_id"] for x in defects["mappings"] if cid in x["required_coupling_system_ids"]]
        t["status"]="COUPLING_ZONE_DECLARATION_DRAFT"
        t["candidate_revision"]=a.candidate; t["candidate_sha256"]=a.sha256; t["pre_edit_candidate_sha256"]=a.sha256
        t["coupling_system_id"]=cid; t["side"]=a.side; t["source_branch"]=a.source_branch
        t["intent"]=f"Execute {pkg['id']} {pkg['name']} at the earliest failing diagnosis layer; no downstream masking."
        t["diagnosis"]["observed_defect_ids"]=linked
        t["diagnosis"]["suspected_layer"]=None
        t["diagnosis"]["human_evidence_ids"]=cp["evidence_ids"]
        t["diagnosis"]["before_evidence"]=[]
        t["proximal_anchor_groups"]=[{"name":x,"bones":[],"expected_behavior":"remain anatomically rooted while sharing deformation with bridge tissue"} for x in cp["proximal_anchors"]]
        t["distal_anchor_groups"]=[{"name":x,"bones":[],"expected_behavior":"follow the anatomically connected distal segment without dragging the whole chain"} for x in cp["distal_anchors"]]
        t["expected_human_behavior"]=cp["must_move"]+["ROOTED: "+x for x in cp["must_remain_rooted"]]
        t["forbidden_visual_failures"]=cp["forbidden_failures"]
        t["repair_package_id"]=pkg["id"]
        t["proof_movements"]=pkg["proof_movements"]
        t["weights_only_acceptance"]=pkg["weights_only_acceptance"]
        t["residual_corrective_role"]=pkg["residual_corrective_role"]
        t["allowed_operations"]=["local_weight_redistribution_after_diagnosis","diagnostic_capture"]
        t["declaration_sources_sha256"]={
          "repair_packages":hashlib.sha256(PACKAGES.read_bytes()).hexdigest(),
          "coupling_map":hashlib.sha256(COUPLING.read_bytes()).hexdigest(),
          "defect_coupling_map":hashlib.sha256(DEFECTS.read_bytes()).hexdigest()
        }
        out=Path(a.out)
        if out.exists(): raise ValueError(f"refusing to overwrite {out}")
        out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(t,indent=2)+"\n",encoding="utf-8")
        print("REPAIR DECLARATION DRAFT WRITTEN",out)
        print(json.dumps({"package":pkg["id"],"coupling_system":cid,"linked_defects":linked,"proof_movements":pkg["proof_movements"]},indent=2))
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
