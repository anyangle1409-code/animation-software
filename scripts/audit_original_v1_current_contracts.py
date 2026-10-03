#!/usr/bin/env python3
"""Audit current ORIGINAL-v1 operational contracts for stale pre-rev2c assumptions.

This is deliberately scoped to live operational tooling/docs, not immutable historical
evidence. It does not edit files or reinterpret old candidate records.
"""
from __future__ import annotations

import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]

FILES=[
    "scripts/original_v1_locked_rig.py",
    "scripts/original_v1_production_control.py",
    "scripts/capture_original_v1_bare_dressed_equivalence_blender.py",
    "scripts/original_v1_bare_dressed_equivalence.py",
    "scripts/smoke_original_v1_candidate_blender.py",
    "scripts/original_v1_phase7_garment_scene.py",
    "scripts/original_v1_garment_evidence.py",
    "scripts/original_v1_dressed_evidence.py",
    "scripts/capture_original_v1_dressed_evidence_blender.py",
    "scripts/original_v1_dressed_range_evidence.py",
    "scripts/capture_original_v1_dressed_range_blender.py",
    "scripts/original_v1_phase6_surface_quality.py",
    "scripts/capture_original_v1_surface_quality_blender.py",
    "scripts/original_v1_phase8_presentation.py",
    "scripts/capture_original_v1_presentation_scene_blender.py",
    "scripts/original_v1_visual_qa.py",
    "scripts/capture_original_v1_visual_qa_masks_blender.py",
    "scripts/capture_original_v1_garment_scene_blender.py",
    "scripts/audit_original_v1_candidate_glbs.py",
    "scripts/export_original_v1_candidate_glb_blender.py",
    "scripts/original_v1_export_evidence.py",
    "scripts/original_v1_runtime_discovery.py",
    "scripts/original_v1_candidate_handoff.py",
    "scripts/verify_original_v1_continuation_decision.py",
    "scripts/select_original_v1_collision_free_revision.py",
    "scripts/original_v1_progress_summary.py",
    "scripts/original_v1_phase5_anatomy.py",
    "scripts/verify_original_v1_final_freeze.py",
    "scripts/verify_original_v1_production_promotion.py",
    "docs/CURRENT_HANDOFF.md",
    "docs/ORIGINAL_V1_PRODUCTION_CONTROL_QUICKSTART.md",
    "docs/work_packages/PHASE_4_DEVELOPMENT_FREEZE.md",
    "docs/work_packages/PHASE_5_ANATOMY_EXECUTION_PROTOCOL.md",
    "docs/work_packages/PHASE_6_TOPOLOGY.md",
    "docs/work_packages/PHASE_7_CLOTHING.md",
    "docs/work_packages/PHASE_8_MATERIALS.md",
    "docs/work_packages/PHASE_9_PRODUCTION_DEFORMATION.md",
    "docs/work_packages/PHASE_10_RUNTIME.md",
    "docs/work_packages/PHASE_11_AUTOMATIC_QA.md",
    "docs/work_packages/VISUAL_QA_PROTOCOL.md",
    "docs/work_packages/PHASE_6_ADVANCED_SURFACE_PROTOCOL.md",
    "docs/work_packages/PHASE_12_PRODUCTION_FREEZE.md",
    "docs/work_packages/RUNTIME_DISCOVERY_HARNESS_PROTOCOL.md",
    "docs/work_packages/LATER_PHASE_EXECUTION_CONTRACT.md",
    "docs/work_packages/LATER_PHASE_TOOLING_READINESS.md",
    "docs/work_packages/CANDIDATE_EXPORT_PROTOCOL.md",
]

FORBIDDEN=[
    (re.compile(r"strict_r2_regression",re.I),"stale strict_r2 regression field"),
    (re.compile(r"(?:len\([^\n]*?\.bones\)|bone_count)\s*(?:==|!=)\s*63\b",re.I),"hard-coded 63-bone operational gate"),
    (re.compile(r"canonical\s+63-bone\s+(?:v4\s+)?rig\s+(?:required|missing)",re.I),"stale 63-bone rig requirement"),
    (re.compile(r"\bcurrent\s+r(?:29|30)\b",re.I),"stale r29/r30 current-candidate prose"),
    (re.compile(r"current[^\n]{0,90}RUN_ORIGINAL_V1_R30\.bat",re.I),"stale r30 current-action prose"),
    (re.compile(r"R2\s+remains\s+the\s+deformation\s+baseline",re.I),"stale R2-only active-baseline prose"),
]


def audit(root:Path=ROOT)->dict:
    issues=[]
    for rel in FILES:
        path=root/rel
        if not path.is_file():
            issues.append({"path":rel,"issue":"protected operational file missing"})
            continue
        body=path.read_text(encoding="utf-8-sig")
        for pattern,label in FORBIDDEN:
            for match in pattern.finditer(body):
                line=body.count("\n",0,match.start())+1
                issues.append({"path":rel,"line":line,"issue":label,"match":match.group(0)})
    lock=root/"ORIGINAL_V1_WORK/SKELETON_MOTION_LOCK_rev2_forearm_twist_only.json"
    if not lock.is_file():
        issues.append({"path":str(lock.relative_to(root)),"issue":"rev2c skeleton-motion lock missing"})
    else:
        data=json.loads(lock.read_text(encoding="utf-8-sig"))
        rig=data.get("rig",{})
        if rig.get("revision")!="rev2_forearm_twist_only" or rig.get("bone_count")!=67 or rig.get("deform_bone_count")!=66:
            issues.append({"path":str(lock.relative_to(root)),"issue":"rev2c lock identity/count differs"})
    return {
        "schema_version":1,
        "status":"CURRENT_CONTRACTS_CLEAN" if not issues else "STALE_CURRENT_CONTRACTS",
        "checked_files":len(FILES),
        "issues":issues,
        "production_approved":False,
        "note":"Current operational-contract guard only; immutable historical evidence is intentionally outside scope.",
    }


def main()->int:
    result=audit(ROOT)
    print(json.dumps(result,indent=2))
    return 0 if not result["issues"] else 1


if __name__=="__main__":
    raise SystemExit(main())
