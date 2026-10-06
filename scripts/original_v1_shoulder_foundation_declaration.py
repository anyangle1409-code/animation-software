#!/usr/bin/env python3
"""Validate fresh descendant shoulder-foundation repair declarations."""
from __future__ import annotations
import json,re
from pathlib import Path
from typing import Any
ISSUES={"WB-AX-001","WB-PEC-002","WB-PEC-003","WB-AX-004","WB-SHO-005","WB-SHO-006","WB-CLV-007","WB-SYM-008"}
PROTECTED={"neck_boundary","pelvis_boundary","hands","feet","head","clothing","unrelated_correctives"}
STOP={"parent_identity_mismatch","out_of_scope_edit","critical_or_high_defect","material_regression","weights_only_visual_failure","axial_rotation_response_failure"}
CAUSAL=["skeleton_mechanics","support_topology","weights_first_transfer","rotation_aware_anatomical_deformation","minimal_residual_correctives"]
def validate_declaration(d:dict[str,Any])->list[str]:
 e=[]
 if d.get("schema_version")!=1:e.append("schema_version must be 1")
 if d.get("declared_before_edit") is not True:e.append("must be declared before edit")
 t=d.get("target_revision");p=d.get("parent",{})
 if not re.fullmatch(r"r\d+",str(t)):e.append("target revision invalid")
 if not re.fullmatch(r"r\d+",str(p.get("revision",""))):e.append("parent revision invalid")
 elif re.fullmatch(r"r\d+",str(t)) and int(t[1:])<=int(p["revision"][1:]):e.append("target must be newer than parent")
 if not re.fullmatch(r"[0-9a-f]{64}",str(p.get("sha256",""))):e.append("parent SHA-256 invalid")
 if set(d.get("issue_ids",[]))!=ISSUES:e.append("linked shoulder issue set incomplete")
 if d.get("acceptance_contract")!="ORIGINAL_V1_SHOULDER_ANATOMICAL_ACCEPTANCE_CONTRACT.json":e.append("acceptance contract binding missing")
 if d.get("causal_order")!=CAUSAL:e.append("causal order changed")
 if not PROTECTED.issubset(set(d.get("protected_zones",[]))):e.append("protected zones incomplete")
 if not STOP.issubset(set(d.get("stop_conditions",[]))):e.append("stop conditions incomplete")
 scope=d.get("scope",{})
 for k in ("permitted_regions","permitted_bones","topology_intent","weight_intent"):
  if not scope.get(k):e.append("scope."+k+" missing")
 if scope.get("weights_only_gate_precedes_correctives") is not True:e.append("weights-only gate must precede correctives")
 if scope.get("exercise_name_driven_deformation_forbidden") is not True:e.append("exercise-name deformation must be forbidden")
 if scope.get("threshold_relaxation_forbidden") is not True:e.append("threshold relaxation must be forbidden")
 return list(dict.fromkeys(e))

def main()->int:
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument("declaration",type=Path);a=ap.parse_args()
 try:data=json.loads(a.declaration.read_text(encoding="utf-8-sig"));errors=validate_declaration(data)
 except (OSError,ValueError,TypeError,json.JSONDecodeError) as exc:
  print("SHOULDER FOUNDATION DECLARATION INVALID: "+str(exc));return 2
 if errors:
  print("SHOULDER FOUNDATION DECLARATION INVALID")
  for x in errors:print("- "+x)
  return 1
 print("SHOULDER FOUNDATION DECLARATION VERIFIED")
 return 0
if __name__=="__main__":raise SystemExit(main())
