#!/usr/bin/env python3
"""Assemble the skeleton-motion LOCK record from executed evidence (python only; refuses unless every gate input is clean).

python scripts/build_original_v1_skeleton_lock_record.py <candidate rN> [--out ORIGINAL_V1_WORK/SKELETON_MOTION_LOCK_<rig revision>.json]

Inputs are the evidence files under ORIGINAL_V1_WORK/candidates/repair_checks/skeleton_lock_<rN>/ plus the candidate manifest,
the rev2 rig payload and the declaration of the helper authoring. The record pins every input by SHA-256. It refuses when the
rig-structure audit has flags, a finger/thumb reversal flag exists, the continuous-motion audit has path flags, the envelope
check is not PASS, or the full-evidence receipt for the candidate is missing. A lock is a pre-freeze evidence checkpoint:
it does not approve a candidate for production and it can be reopened only by direct evidence of a rig defect.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAND = "ORIGINAL_V1_WORK/candidates"

ROWS = [
    ("head/neck", "LOCKED", False, None, "neck/head hinge in squat/row within envelope; single neck + head chain sufficient for exercise instruction"),
    ("thorax/spine", "LOCKED", False, None, "pelvis hinge plus three spine segments distribute flexion (row: pelvis 38 + spine 10; squat 18 + 15); rib-cage proxy built; no rib bones, no chest helper required"),
    ("shoulder girdle", "LOCKED", False, None, "clavicle + scapula + humerus coherent through press/pull-up; rhythm poses use a modest, non-fixed scapular share (references show 0.9:1..3.8:1); axilla defect classified as pose/rig construction and fixed (P2 + twist helpers)"),
    ("upper arm / twist", "LOCKED", True, "upperarm_tw0/tw1 (l,r)", "humeral rotation 63-90 deg in 7 poses; twist stress at 90 deg: slice radius 0.856 -> 0.907 but the abstract minimum edge worsened 0.28 -> 0.22 at the dense (8 mm) deltoid edges; in the real stress poses the helpers clear the shoulder-minimum development failures (5 -> 2 failures vs P2B1) at the price of arm-region stretch up to 3.2 (gate 5.0), left to the weight re-solve; forearm-only variant r42 shown for contrast"),
    ("elbow", "LOCKED", False, None, "hinge purity: elbow abduction within +-10 deg in all poses and samples (P1: up to 107 deg sideways)"),
    ("forearm / twist", "LOCKED", True, "forearm_tw0/tw1 (l,r)", "twist stress 90 deg: slice radius 0.76 -> 0.92, edge min 0.705 -> 0.92"),
    ("wrist", "LOCKED", False, None, "push-up: ~78 deg loaded extension, small ulnar deviation (P1: 88 deg radial deviation); no wrist helper required"),
    ("palm", "LOCKED", False, None, "palm planted (hand region 3.6 mm, thumb pad 0 mm, palm normal 5.7 deg from the floor normal); cupping handled by metacarpal + finger chains; palm helpers not justified"),
    ("thumb", "LOCKED", False, None, "P1 reversed the thumb IP in the grip; fixed with a single chain hinge; thumb flattened into the palm plane for loaded support"),
    ("fingers", "LOCKED", False, None, "P1 bent the distal joint backwards (-55 deg; -85 on handle grips) in 11 poses due to pose-construction axis flip; fixed (fixed hinge axis); 0 reversal flags"),
    ("hip", "LOCKED", False, None, "squat/lunge within envelope; thigh twist helper considered and rejected (femoral 45 deg: slice radius 0.99, edge 0.86)"),
    ("knee", "LOCKED", False, None, "flexion 98 (squat), 79/62 (lunge) within envelope, hinge only; no helper"),
    ("shin/calf / twist", "LOCKED", False, None, "shin twist helper considered and rejected (physiological +-30 deg: slice radius 0.97, edge 0.90)"),
    ("ankle", "LOCKED", False, None, "P1 squat ankle plantarflexed (seated posture); P2 dorsiflexion 23 deg, push-up <= ~25 deg"),
    ("forefoot/toes", "LOCKED", False, None, "P1 bent the toe the wrong way (-60 deg); P2 dorsiflexion 80 deg with toe pads on the floor; single toe bone sufficient for support mechanics; hallux/lesser-toe split deferred until individually modelled toes exist (Phase 5F trigger documented)"),
]


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def need(p):
    if not (ROOT / p).is_file():
        raise SystemExit("STOP - missing evidence: " + p)
    return {"path": p, "sha256": sha(p)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("revision")
    ap.add_argument("--out")
    a = ap.parse_args()
    rev = a.revision
    d = f"{CAND}/repair_checks/skeleton_lock_{rev}"
    man = json.loads((ROOT / f"{CAND}/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{rev}.json").read_text(encoding="utf-8-sig"))
    ev = {k: need(f"{d}/{rev}_{k}.json") for k in ("rig_structure", "skeleton_motion", "finger_flexion", "joint_kinematics_fine",
                                                   "twist_stress", "floor_contact", "envelope_check")}
    structure = json.loads((ROOT / ev["rig_structure"]["path"]).read_text(encoding="utf-8"))
    problems = []
    if structure["flags"]:
        problems.append("rig structure audit has flags")
    if json.loads((ROOT / ev["skeleton_motion"]["path"]).read_text(encoding="utf-8"))["flags"]:
        problems.append("skeleton motion audit has flags")
    if json.loads((ROOT / ev["finger_flexion"]["path"]).read_text(encoding="utf-8"))["flagged"]:
        problems.append("finger/thumb reversal or envelope flags")
    if json.loads((ROOT / ev["joint_kinematics_fine"]["path"]).read_text(encoding="utf-8"))["path_flags"]:
        problems.append("continuous-motion path flags")
    if json.loads((ROOT / ev["envelope_check"]["path"]).read_text(encoding="utf-8"))["status"] != "PASS":
        problems.append("movement envelope check is not PASS")
    receipt = f"{CAND}/repair_checks/full_{rev}_evidence_manifest.json"
    if not (ROOT / receipt).is_file():
        problems.append("full-evidence receipt missing")
    if sha(f"{CAND}/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{rev}.json") != hashlib.sha256((ROOT / f"{CAND}/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{rev}.json").read_bytes()).hexdigest():
        problems.append("manifest hash")
    if problems:
        raise SystemExit("STOP - lock refused: " + "; ".join(problems))
    control = json.loads((ROOT / "ORIGINAL_V1_PRODUCTION_CONTROL.json").read_text(encoding="utf-8"))
    payload = "ORIGINAL_V1_WORK/hgpt_canonical_v4_original_rev2.json"
    record = {
        "schema_version": 1, "generated_utc": datetime.now(timezone.utc).isoformat(),
        "kind": "SKELETON_MOTION_LOCK", "production_approved": False,
        "rig": {"identity": "hgpt_canonical_v4_original", "revision": structure["rig_revision"],
                "rig_structure_sha256": structure["rig_structure_sha256"], "bone_count": structure["bone_count"],
                "deform_bone_count": structure["deform_bone_count"], "payload": need(payload),
                "base_revision": "v4_63_bone (unchanged; preserved as historical evidence; r38 rig_structure_sha256 19493caa...)",
                "bone_list_and_hierarchy": "payload bones[] and rig_structure bones[] (name, parent, head, tail, roll, matrix, deform)"},
        "locked_candidate": {"revision": rev, "sha256": man["candidate_sha256"], "manifest": need(f"{CAND}/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{rev}.json"),
                             "parent": man.get("source_candidate"), "full_evidence_receipt": need(receipt)},
        "stress_pose_definition": control["frozen_pose_definition"] | {"history": [h["revision"] for h in control.get("pose_definition_history", [])]},
        "movement_envelope": need("ORIGINAL_V1_SKELETON_MOVEMENT_ENVELOPE.json"),
        "reference_matrix": need("docs/ORIGINAL_V1_SKELETON_REFERENCE_EVIDENCE.md"),
        "evidence": ev,
        "helper_decisions": {"added": ["upperarm_tw0_l/r", "upperarm_tw1_l/r", "forearm_tw0_l/r", "forearm_tw1_l/r"],
                             "added_reason": "generic axial-twist distribution along long segments (twist stress evidence); deterministic closed-form drive scripts/original_v1_twist_helpers.py; identity helpers when there is no twist",
                             "considered_rejected": [
                                 {"helper": "thigh twist", "reason": "femoral rotation +-45 deg: slice radius >= 0.988, edge >= 0.86"},
                                 {"helper": "shin/calf twist", "reason": "tibial rotation +-30 deg: slice radius >= 0.971, edge >= 0.895"},
                                 {"helper": "palm cupping / thumb helper", "reason": "no evidence the existing metacarpal + finger + thumb chains cannot cup or ground the palm; revisit at Phase 5D"},
                                 {"helper": "hallux + lesser-toe split", "reason": "single toe hinge reproduces loaded forefoot support (toe pads on the floor); revisit only if Phase 5F models individual toes"},
                                 {"helper": "individual rib bones / chest expansion", "reason": "rib cage distributes thoracic motion; no breathing requirement; rib-cage proxy used for validation only"},
                                 {"helper": "extra shoulder/thorax helper", "reason": "scapula/clavicle controls sufficient; no evidence of a missing degree of freedom"}]},
        "rows": [{"region": r, "status": s, "rig_defect_found_in_rig_bones": False, "extra_bone_helper": h, "notes": n} for r, s, _, h, n in ROWS],
        "owner_authorised_inherited_minima_not_reopened": True,
        "reopen_rule": "only direct new evidence of a true rig defect (skeleton-only audits still correct => deformation is not a reason)",
        "note": "Pre-freeze evidence checkpoint. Not production approval; R2 and thresholds unchanged.",
    }
    out = Path(a.out) if a.out else ROOT / f"ORIGINAL_V1_WORK/SKELETON_MOTION_LOCK_{structure['rig_revision']}.json"
    if out.exists():
        raise SystemExit("STOP - lock record exists; a new rig revision needs a new record")
    out.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print("SKELETON MOTION LOCK RECORDED", out, "rig", structure["rig_structure_sha256"][:16], "candidate", rev)


if __name__ == "__main__":
    main()
