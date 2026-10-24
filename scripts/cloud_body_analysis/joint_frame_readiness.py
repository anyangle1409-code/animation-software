"""Fail-closed ISB-inspired frame/movement dependency report; no model editing.

A dependency report is NOT a measured joint-coordinate frame, pose trial,
anatomical side determination, or acceptance of skin deformation.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROM = ROOT / "docs/anatomy/HGPT_HUMAN_JOINT_ROM_REFERENCE_V1.json"
LANDMARKS = ROOT / "docs/anatomy/HGPT_ISB_LANDMARK_REQUIREMENTS_V1.json"
LEDGER = ROOT / "docs/anatomy/HGPT_HUMAN_MOTION_TEST_EXECUTION_LEDGER_V1.json"

# Conservative prerequisites for triage, NOT exact ISB segment-frame definitions.
# Missing segments expose checklist gaps rather than manufacturing landmarks.
FAMILY_PREREQUISITES = {
    "glenohumeral": (("scapula", "humerus"), ()),
    "scapula": (("thorax", "scapula"), ()),
    "clavicle": (("thorax", "clavicle"), ()),
    "shoulder": (("thorax", "scapula", "clavicle", "humerus"), ()),
    "elbow": (("humerus", "forearm"), ("ulna_proximal",)),
    "radioulnar": (("forearm",), ("radius_segment", "ulna_segment")),
    "wrist": (("forearm",), ("hand_segment",)),
    "finger": ((), ("finger_segments",)),
    "thumb": ((), ("thumb_segments",)),
    "cervical": (("thorax",), ("cervical_segment",)),
    "thoracolumbar": (("thorax", "pelvis"), ("lumbar_segment",)),
    "trunk": (("thorax", "pelvis"), ("lumbar_segment",)),
    "hip": (("pelvis", "femur"), ()),
    "lumbopelvic": (("pelvis",), ("lumbar_segment",)),
    "knee": (("femur",), ("tibia_segment",)),
    "patellofemoral": (("femur",), ("patella_segment",)),
    "talocrural": (("ankle", "foot"), ("tibia_segment",)),
    "ankle": (("ankle", "foot"), ("tibia_segment",)),
    "subtalar": (("ankle", "foot"), ("hindfoot_frame",)),
    "midtarsal": (("foot",), ("midfoot_frame",)),
    "metatarsophalangeal": (("foot",), ("toe_segment",)),
    "foot": (("foot",), ("hindfoot_frame", "midfoot_frame", "forefoot_frame")),
}
UNBOUND = ("model_bone_id", "model_mesh_vertex_id", "model_coordinate_body_local_m",
           "coordinate_frame", "reviewed_attachment_region", "model_source_sha256",
           "independent_side_evidence")
UNAPPROVED = ("anatomical_side_verified", "landmark_verified", "muscle_attachment_authorized")
PINNED_MODELS = {
    "W8": "2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c",
    "V14": "5969aa98122e267b6bdd94fdfaf6d2877a1b27f7ea8d11c6a8e078b467b0ff91",
    "R120": "fb3b0acfc68bc59952b0fc6c45f7d7715717207fd9ba0b7f2b124e905ce2ddcb",
}

def expand_required_id(label, side):
    return "hgpt.landmark." + label + ("" if label.endswith(".MIDLINE") else "." + side)

def audit(rom, landmarks, ledger, rig):
    if (rom.get("rom_mean_is_a_hard_limit") is not False
        or rom.get("clinical_confidence_interval_is_an_individual_limit") is not False):
        raise ValueError("clinical means/confidence intervals cannot be hard limits")
    if landmarks.get("native_bindings_approved") is not False or landmarks.get("hard_limits_approved") is not False:
        raise ValueError("unearned landmark or ROM approval")
    if (ledger.get("clinical_rom_hard_limits_applied") is not False
        or ledger.get("anatomical_side_approved") is not False
        or ledger.get("production_deployed") is not False):
        raise ValueError("unearned movement approval")
    if (rig.get("source_sha256") != PINNED_MODELS or rig.get("all_three_identical") is not True
        or any(rig.get(k) is not False for k in
               ("anatomical_side_verified", "isb_joint_axes_calibrated",
                "human_joint_rom_limits_approved", "skin_deformation_approved"))
        or rig.get("bone_counts") != {"W8": 77, "V14": 77, "R120": 77}):
        raise ValueError("missing/mismatched pinned native rest rig evidence")
    if len(rig.get("metadata_fingerprints_sha256", {})) != 3:
        raise ValueError("missing rig metadata fingerprints")
    entries = landmarks.get("landmarks", [])
    if len(entries) != landmarks.get("landmark_count") or len(entries) != 46:
        raise ValueError("landmark registry count mismatch")
    ids = [x.get("id") for x in entries]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate landmark IDs")
    by_id = {x["id"]: x for x in entries}
    for item in entries:
        if any(item.get(k) is not None for k in UNBOUND) or any(item.get(k) is not False for k in UNAPPROVED):
            raise ValueError("unreviewed landmark must remain unbound and unapproved")
    segment_specs = {x["id"].removeprefix("hgpt.segment."): x for x in landmarks["segment_requirements"]}
    if any(x.get("isb_axes_defined") is not False for x in segment_specs.values()):
        raise ValueError("unearned anatomical segment frame")
    planned = rom.get("motion_test_program", [])
    records = ledger.get("tests", [])
    if (len(planned) != 19 or len(records) != 19
        or len({x["id"] for x in planned}) != 19
        or {x["id"] for x in planned} != {x["id"] for x in records}
        or ledger.get("summary", {}).get("generic_tests_executed") != 0
        or ledger.get("summary", {}).get("generic_tests_passed") != 0):
        raise ValueError("generic motion suite evidence not in expected unexecuted state")
    record_map = {x["id"]: x for x in records}
    results = []
    for scenario in planned:
        record = record_map[scenario["id"]]
        if (record.get("generic_joint_suite_status") != "NOT_RUN"
            or any(record.get(k) is not False for k in
                   ("blender_joint_axes_calibrated", "individual_joint_motion_validated",
                    "skin_contact_validated", "phone_review_accepted", "exercise_approved"))
            or scenario.get("blender_pose_recipe") is not None
            or scenario.get("actual_joint_measurement_status") != "NOT_MEASURED"
            or scenario.get("native_acceptance") != "NOT_GRANTED"):
            raise ValueError("motion scenario cannot be presented as executed or approved")
        families = scenario["required_joint_families"]
        unknown = sorted(set(families) - set(FAMILY_PREREQUISITES))
        if unknown:
            raise ValueError("unknown joint family, add explicit conservative prerequisites: " + ", ".join(unknown))
        segments = sorted({seg for f in families for seg in FAMILY_PREREQUISITES[f][0]})
        absent_frames = sorted({seg for f in families for seg in FAMILY_PREREQUISITES[f][1]})
        if set(segments) - set(segment_specs):
            raise ValueError("unknown landmark segment checklist requirement")
        required_ids = set()
        for seg in segments:
            for label in segment_specs[seg]["required_landmarks"]:
                sides = ("MIDLINE",) if label.endswith(".MIDLINE") else (("L", "R") if scenario["side_scope"] == "both" else ("MIDLINE",))
                for side in sides:
                    full = expand_required_id(label, side)
                    if full not in by_id:
                        raise ValueError("missing required landmark " + full)
                    required_ids.add(full)
        results.append({
            "id": scenario["id"], "region": scenario["region"],
            "required_joint_families": families, "checklist_segments": segments,
            "unrepresented_segment_frames": absent_frames,
            "required_unbound_landmark_ids": sorted(required_ids),
            "unbound_landmark_count": len(required_ids),
            "segment_frame_axes_unverified": segments,
            "existing_related_benchmark_status": record["related_prior_benchmark_status"],
            "generic_motion_test_status": "NOT_RUN",
            "joint_frame_readiness": "BLOCKED_UNBOUND_LANDMARKS_AND_UNVERIFIED_AXES",
            "skin_continuity": "NOT_TESTED_IN_GENERIC_SUITE",
            "contact_and_human_visual_acceptance": "NOT_GRANTED",
        })
    return {
        "status": "READ_ONLY_ISB_DEPENDENCY_GAPS_NO_ANATOMICAL_CALIBRATION",
        "source_model_sha256": PINNED_MODELS,
        "rig_metadata_fingerprints_sha256": rig["metadata_fingerprints_sha256"],
        "rig_rest_metadata_identical": True,
        "landmark_count": len(entries),
        "bound_landmarks": 0,
        "planned_generic_motion_tests": len(results),
        "generic_motion_tests_executed": 0,
        "generic_motion_tests_approved": 0,
        "joint_coordinate_frames_approved": False,
        "skin_deformation_approved": False,
        "muscle_attachments_approved": False,
        "clinical_rom_means_as_limits": False,
        "muscle_highlighting_implemented": False,
        "scenarios": results,
        "sources": landmarks["sources"],
        "limitations": [
            "Conservative dependency crosswalk, not verbatim ISB axis construction.",
            "Bone-local rest XYZ, authored bone heads, and suffix names are not anatomical frames or sides.",
            "Checklist lower-limb and foot points include proposed review candidates, not certified ISB definitions.",
            "No new pose, forearm pronation, skin strain, contact, muscle, or exercise tests were executed.",
            "Existing shoulder press/squat/grip failures remain separate native benchmark evidence.",
            "Clinical ROM population means and confidence intervals are not movement clamps.",
        ],
    }

def markdown(report):
    lines = ["# Phone joint-coordinate and movement readiness", "",
             "**NO ANATOMICAL CALIBRATION / NO GENERIC MOTION TEST APPROVAL.**", "",
             f"Rest rig: W8/V14/R120 identical metadata, 77 bones each; {report['bound_landmarks']}/{report['landmark_count']} reviewed landmarks bound.",
             f"Generic motion scenarios executed/approved: 0/{report['planned_generic_motion_tests']}.", "",
             "| Scenario | Missing landmarks | Missing frame categories | Status |",
             "|---|---:|---|---|"]
    for row in report["scenarios"]:
        name = row["id"].removeprefix("hgpt.motion_test.")
        frames = ", ".join(row["unrepresented_segment_frames"]) or "none listed"
        lines.append(f"| {name} | {row['unbound_landmark_count']} | {frames} | BLOCKED |")
    lines += ["", "Every checklist segment frame is unverified; the table lists triage dependencies only.",
              "The prior shoulder press/squat/grip failures are NOT generic test passes.",
              "Do not infer side or muscle attachments, or clamp to CDC population means.", ""]
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rig-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    from compare_rig_axes import compare
    from isb_landmark_requirements import load as load_landmarks
    rig = compare(args.rig_root)
    landmarks = load_landmarks(LANDMARKS)
    report = audit(json.loads(ROM.read_text()), landmarks, json.loads(LEDGER.read_text()), rig)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "joint_frame_readiness.json").write_text(json.dumps(report, indent=2) + "\n")
    (args.out / "joint_frame_readiness.md").write_text(markdown(report))
    print(report["status"], report["planned_generic_motion_tests"], "BLOCKED")

if __name__ == "__main__":
    main()
