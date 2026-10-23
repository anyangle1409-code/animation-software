"""Source-backed human joint motion reference: REPORT ONLY, never a safety clamp.

The CDC 20–44/45–69 joint ROM values are age/sex group means and CI for
those means. They are *not* individual limits, exercise safety envelopes,
or the 3D axes of the author's Blender rig.

No bpy dependency and NO geometry modification or app runtime integration.
"""
import argparse
import json
import math
from pathlib import Path

REFERENCE = Path(__file__).resolve().parents[2] / "docs" / "anatomy" / "HGPT_HUMAN_JOINT_ROM_REFERENCE_V1.json"
BANDS = {"20_44", "45_69"}
GROUPS = {"female", "male"}
EXPECTED_MOTIONS = {
    "hip_extension", "hip_flexion", "knee_flexion", "knee_extension",
    "ankle_dorsiflexion", "ankle_plantarflexion", "shoulder_flexion",
    "elbow_flexion", "elbow_extension", "forearm_pronation", "forearm_supination",
}

def finite_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)

def validate(document):
    errors = []
    if not isinstance(document, dict):
        return ["reference must be a JSON object"]
    if document.get("schema_version") != 1 or document.get("artifact_type") != "human_joint_motion_research_reference":
        errors.append("invalid version/artifact type")
    if document.get("angle_unit") != "degree":
        errors.append("angle unit must be degrees")
    if document.get("rom_mean_is_a_hard_limit") is not False:
        errors.append("clinical population mean must NEVER be a hard limit")
    if document.get("clinical_confidence_interval_is_an_individual_limit") is not False:
        errors.append("CI for mean must NEVER be individual ROM envelope")
    if document.get("model_adoption") != "NOT_GRANTED":
        errors.append("cannot grant native anatomy approval")

    sources = document.get("sources", [])
    sid = [s.get("id") for s in sources if isinstance(s, dict)]
    if len(sid) != len(set(sid)) or len(sid) < 4:
        errors.append("missing/duplicate provenance sources")
    for s in sources:
        if (not isinstance(s, dict) or not str(s.get("url", "")).startswith("https://")
            or s.get("reference_only") is not True):
            errors.append("invalid source URL or missing reference-only flag")
    if not {"cdc_joint_rom_soucie2010", "isb_joint_coordinate_part1", "isb_joint_coordinate_part2"}.issubset(set(sid)):
        errors.append("CDC/ISB primary sources absent")

    pop = document.get("population_statistics", {})
    if pop.get("population_source") != "cdc_joint_rom_soucie2010":
        errors.append("wrong clinical reference provenance")
    observed = set()
    for row in pop.get("measurements", []):
        if not isinstance(row, dict):
            errors.append("malformed CDC row")
            continue
        key = (row.get("movement"), row.get("age_band"), row.get("reference_group"))
        if key in observed:
            errors.append("duplicate clinical reference group")
        observed.add(key)
        if (key[0] not in EXPECTED_MOTIONS or key[1] not in BANDS or key[2] not in GROUPS):
            errors.append("unknown CDC motion, age or group")
        if row.get("source_id") != "cdc_joint_rom_soucie2010":
            errors.append("CDC reference source mismatch")
        mean, ci = row.get("mean_deg"), row.get("ci95_for_population_mean_deg")
        if (not finite_number(mean) or not isinstance(ci, list) or len(ci) != 2
            or not all(finite_number(x) for x in ci) or ci[0] > ci[1]
            or (finite_number(mean) and not ci[0] <= mean <= ci[1])):
            errors.append("nonfinite/misordered CDC mean or confidence interval")
    expected = {(m, age, group) for m in EXPECTED_MOTIONS for age in BANDS for group in GROUPS}
    if observed != expected:
        errors.append("incomplete adult reference coverage")

    coords = document.get("coordinate_catalog", [])
    coordids = set()
    for item in coords:
        if not isinstance(item, dict):
            errors.append("malformed coordinate")
            continue
        key = item.get("id")
        if key in coordids:
            errors.append("duplicate joint coordinate")
        coordids.add(key)
        if not isinstance(key, str) or not key.startswith("hgpt.coordinate."):
            errors.append("coordinate has no permanent semantic ID")
        if item.get("cdc_reference_key") is not None and item["cdc_reference_key"] not in EXPECTED_MOTIONS:
            errors.append("coordinate references unknown clinical measurement")
        if (item.get("hard_lower_limit_deg") is not None or item.get("hard_upper_limit_deg") is not None):
            errors.append("unreviewed clinical averages cannot create hard joint limits")
        if (item.get("rig_axis_binding") is not None or item.get("anatomical_side_mapping") is not None
            or item.get("approval") != "NOT_GRANTED"):
            errors.append("unverified rig axis/side or approval must fail closed")
    if len(coordids) < 40:
        errors.append("incomplete multisegment body coordinate catalogue")
    by_name = {c["id"]: c for c in coords if isinstance(c, dict) and isinstance(c.get("id"), str)}
    shoulder = by_name.get("hgpt.coordinate.shoulder_complex_flexion", {})
    gh = by_name.get("hgpt.coordinate.glenohumeral_flexion", {})
    if shoulder.get("cdc_reference_key") != "shoulder_flexion" or gh.get("cdc_reference_key") is not None:
        errors.append("do not confuse CDC shoulder complex with isolated GH flexion")

    coupling = document.get("coupling_rules", [])
    ids = [c.get("id") for c in coupling if isinstance(c, dict)]
    if len(ids) != len(set(ids)) or "shoulder_complex_requires_scaps" not in ids:
        errors.append("missing/duplicate kinematic coupling")
    for rule in coupling:
        if not isinstance(rule, dict):
            errors.append("malformed coupling")
            continue
        if any(ref not in sid for ref in rule.get("source_ids", [])):
            errors.append("coupling cites unknown source")
        if not str(rule.get("solver_constraint", "")).startswith("UNDEFINED_"):
            errors.append("unverified coupling must not claim a numeric solver constraint")

    # Secondary nominal AAOS-style norms and a different age-restricted spine
    # cohort are informative but CANNOT be merged into the CDC reference
    # distribution, or used to assign per-vertebra or shoulder-hinge limits.
    context = document.get("secondary_reference_context", {})
    if context.get("safety_approval") != "NOT_GRANTED":
        errors.append("secondary context cannot claim safety approval")
    for key, expected_source, expected_size in (
            ("aaos_illustrative_goniometry", "norkin_white_goniometry_6e", 12),
            ("young_adult_spine_means", "young_adult_spine_goniometry_2023", 12)):
        values = context.get(key, [])
        if len(values) != expected_size:
            errors.append(key + ": incomplete source-specific series")
        names = set()
        for record in values:
            if not isinstance(record, dict):
                errors.append(key + ": invalid record")
                continue
            motion = record.get("movement")
            if motion in names:
                errors.append(key + ": duplicate motion")
            names.add(motion)
            if (not motion or record.get("source_id") != expected_source
                or record.get("hard_limit") is not False):
                errors.append(key + ": source/limit guard")
            if key == "aaos_illustrative_goniometry":
                if not finite_number(record.get("nominal_deg")) or record.get("evidence_class") != "AAOS_table_illustrative_goniometric_normative_value":
                    errors.append(key + ": invalid nominal context")
            else:
                if (not finite_number(record.get("mean_deg")) or
                    not finite_number(record.get("sd_deg")) or record["sd_deg"] <= 0
                    or record.get("evidence_class") != "clinical_group_mean_plus_SD_not_bone_level_range"):
                    errors.append(key + ": invalid SD/mean context")

    tests = document.get("motion_test_program", [])
    testids = [t.get("id") for t in tests if isinstance(t, dict)]
    if len(testids) != len(set(testids)) or len(testids) < 15:
        errors.append("insufficient or duplicate motion tests")
    for t in tests:
        if not isinstance(t, dict):
            errors.append("malformed test programme")
            continue
        if (t.get("blender_pose_recipe") is not None or t.get("actual_joint_measurement_status") != "NOT_MEASURED"
            or t.get("native_acceptance") != "NOT_GRANTED"
            or t.get("model_source_hash") is not None or t.get("review_render_artifact") is not None):
            errors.append("never confuse a conceptual joint test with executed Blender validation")
        if not isinstance(t.get("conceptual_samples"), list) or len(t["conceptual_samples"]) < 3:
            errors.append("motion test lacks meaningful movement samples")
        if t.get("side_scope") not in {"both", "midline"}:
            errors.append("invalid side scope")
    needed = {"elbow_flexion_supinated", "forearm_rotation", "shoulder_flexion",
              "hip_flexion_extension", "knee_flexion_extension", "ankle_dorsi_plantarflexion",
              "compound_overhead_press", "compound_squat", "compound_dumbbell_curl"}
    if not {"hgpt.motion_test." + k for k in needed}.issubset(testids):
        errors.append("essential generic/compound movement tests missing")
    if document.get("future_display", {}).get("muscle_highlighting") != "DEFERRED_BY_OWNER":
        errors.append("muscle highlight appearance/implementation not authorized")
    return errors

def load_reference(path=REFERENCE):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    errors = validate(data)
    if errors:
        raise ValueError("Invalid research reference: " + "; ".join(errors))
    return data

def compare_population_mean(data, movement, group, age_band, observed_deg):
    """Pure reference comparison: NEVER a safety or biomechanical pass/fail."""
    if not finite_number(observed_deg):
        raise ValueError("observed degrees must be a finite numeric value")
    if movement not in EXPECTED_MOTIONS or group not in GROUPS or age_band not in BANDS:
        raise ValueError("unknown motion or population reference")
    row = next(v for v in data["population_statistics"]["measurements"] if
               v["movement"] == movement and v["reference_group"] == group and v["age_band"] == age_band)
    return {
        "motion": movement, "group": group, "age_band": age_band,
        "observed_deg": float(observed_deg), "group_mean_deg": row["mean_deg"],
        "difference_from_group_mean_deg": round(float(observed_deg) - row["mean_deg"], 4),
        "confidence_interval_for_group_mean_deg": row["ci95_for_population_mean_deg"],
        "source": row["source_id"],
        "safety_limit_test": False, "individual_possible_range": None,
        "native_anatomical_joint_mapping": "UNVERIFIED",
        "result": "DESCRIPTIVE_COMPARISON_ONLY_NOT_EXERCISE_APPROVAL",
    }

def readiness(data):
    """Readiness here means the *reference is usable*, not the model approved."""
    return {
        "source_backed_reference_ready": not validate(data),
        "cdc_group_statistics_count": len(data["population_statistics"]["measurements"]),
        "named_joint_coordinates": len(data["coordinate_catalog"]),
        "conceptual_pose_tests": len(data["motion_test_program"]),
        "native_coordinate_calibration": "NOT_GRANTED",
        "measured_joint_trajectory_tests": "NOT_RUN",
        "shape_and_contact_validation": "NOT_RUN",
        "realistic_human_motion_approval": "NOT_GRANTED",
        "hard_joint_limits_approved": 0,
        "muscle_highlighting": "DEFERRED_BY_OWNER",
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--reference", type=Path, default=REFERENCE)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    data = load_reference(args.reference)
    result = readiness(data)
    payload = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")

if __name__ == "__main__":
    main()
