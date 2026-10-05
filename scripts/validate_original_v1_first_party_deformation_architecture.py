#!/usr/bin/env python3
"""Validate the ORIGINAL-v1 first-party deformation architecture."""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ARCH=ROOT/"ORIGINAL_V1_FIRST_PARTY_DEFORMATION_ARCHITECTURE.json"
MASTER=ROOT/"ORIGINAL_V1_HUMAN_BODY_MASTER_PLAN.json"
COUPLING=ROOT/"ORIGINAL_V1_ANATOMICAL_COUPLING_MAP.json"
TRIGGERS=ROOT/"ORIGINAL_V1_JOINT_TISSUE_TRIGGER_MAP.json"

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def validate(a,m,c,t):
    if a.get("schema_version")!=1: raise ValueError("schema_version must be 1")
    if a.get("status")!="AUTHORITATIVE_FIRST_PARTY_DEFORMATION_ARCHITECTURE":
        raise ValueError("unexpected architecture status")
    if a.get("production_approved") is not False:
        raise ValueError("architecture may not claim production approval")
    if a.get("asset")!=m.get("asset") or a.get("rig")!=m.get("rig"):
        raise ValueError("asset/rig identity differs from master plan")
    if a.get("coupling_map")!="ORIGINAL_V1_ANATOMICAL_COUPLING_MAP.json":
        raise ValueError("coupling map authority differs")
    if a.get("joint_tissue_trigger_map")!="ORIGINAL_V1_JOINT_TISSUE_TRIGGER_MAP.json":
        raise ValueError("joint trigger authority differs")

    stack=a.get("stack") or []
    orders=[x.get("order") for x in stack]
    if orders!=list(range(6)): raise ValueError("deformation stack must have orders 0..5 exactly")
    ids=[x.get("id") for x in stack]
    expected=["kinematics","base_skinning","anatomical_coupling","pose_space_correction","contact_load_response","secondary_soft_tissue"]
    if ids!=expected: raise ValueError("deformation stack order/identity differs")

    inv="\n".join(a.get("hard_invariants") or []).lower()
    for phrase in (
        "no deformation driver may branch on an exercise name",
        "weights-only",
        "multi-anchor",
        "same joint state",
        "runtime and blender",
    ):
        if phrase not in inv: raise ValueError("missing hard invariant: "+phrase)

    contract=a.get("generic_driver_contract") or {}
    forbidden=set(contract.get("forbidden_inputs") or [])
    if not {"exercise_name","exercise_id","hard_coded_pose_name_as_runtime_logic"}.issubset(forbidden):
        raise ValueError("exercise identity not fully forbidden from runtime deformation")
    permitted=set(contract.get("permitted_inputs") or [])
    for key in ("canonical_bone_transforms","relative_anchor_transforms","joint_angles_derived_from_canonical_transforms"):
        if key not in permitted: raise ValueError("generic driver missing permitted input "+key)

    base=next(x for x in stack if x["id"]=="base_skinning")
    candidates=set(base.get("candidates") or [])
    if not {"linear_blend_skinning","dual_quaternion_or_preserve_volume"}.issubset(candidates):
        raise ValueError("base-skinning evidence candidates incomplete")
    if "UNRESOLVED" not in base.get("current_decision",""):
        raise ValueError("base skinning must remain unresolved until evidence is captured")

    ab=a.get("base_skinning_selection_gate") or {}
    controls=set(ab.get("required_controls") or [])
    for item in ("same_exact_source_candidate_copy","same_rest_mesh","same_rig","same_pose_definition","same_weights","same_render_settings"):
        if item not in controls: raise ValueError("A/B selection control missing "+item)
    if "whole-body evidence" not in ab.get("decision_rule","").lower():
        raise ValueError("A/B selection must be whole-body evidence driven")

    parity=a.get("production_parity_gate") or {}
    if parity.get("blender_reference_required") is not True or parity.get("standalone_runtime_required") is not True:
        raise ValueError("Blender/runtime parity requirement incomplete")
    if not parity.get("production_blocker"): raise ValueError("production parity blocker missing")

    # Structural authorities themselves must still be nonempty/validly shaped.
    if not c.get("coupling_systems"): raise ValueError("coupling systems missing")
    if not t.get("rules"): raise ValueError("joint-tissue trigger rules missing")
    return True

def main():
    try:
        validate(read(ARCH),read(MASTER),read(COUPLING),read(TRIGGERS))
        print("FIRST-PARTY DEFORMATION ARCHITECTURE: PASS")
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2

if __name__=="__main__": raise SystemExit(main())
