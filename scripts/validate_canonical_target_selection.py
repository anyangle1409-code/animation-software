import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SEL = ROOT / "ORIGINAL_V1_WORK/anatomy/canonical_target_selection_v1.json"
CONV = ROOT / "ORIGINAL_V1_WORK/anatomy/canonical_evidence_convergence_v1.json"
CORR = ROOT / "ORIGINAL_V1_WORK/anatomy/canonical_target_corridors_v1.json"
SHOULDER_CONSTRAINT = ROOT / "ORIGINAL_V1_WORK/anatomy/canonical_shoulder_target_constraints_v1.json"
SHOULDER_SOURCE = ROOT / "ORIGINAL_V1_WORK/anatomy/canonical_shoulder_constraint_sources_v1.json"

REQUIRED_REGIONS = {
    "shoulder_girdle",
    "spine",
    "ribs",
    "forearm",
    "carpus_hand",
    "pelvis",
    "lower_limb_long",
    "tarsus_forefoot",
    "head_neck",
}


def load(path):
    return json.loads(path.read_text())


def _contains_unresolved_grade(value):
    """Return True if an evidence-grade field still contains a C/D grade.

    Grades are sometimes stored as strings and sometimes as region sub-maps.
    Prefix matching deliberately accepts qualified A/B labels while rejecting
    unresolved C/D states when freeze_ready is asserted.
    """
    if isinstance(value, dict):
        return any(_contains_unresolved_grade(v) for v in value.values())
    if isinstance(value, list):
        return any(_contains_unresolved_grade(v) for v in value)
    if isinstance(value, str):
        return value.startswith("C") or value.startswith("D")
    return False


def _null_paths(obj, path="selected"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _null_paths(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _null_paths(v, f"{path}[{i}]")
    elif obj is None:
        yield path


def validate(s, conv, corr, shoulder_constraint=None, shoulder_source=None):
    errors = []
    warnings = []

    if set(s["regions"]) != REQUIRED_REGIONS:
        errors.append(f"region set mismatch: {set(s['regions']) ^ REQUIRED_REGIONS}")

    # freeze_ready is a deliberately hard gate. A future promotion must clear
    # blockers, null target fields and unresolved C/D evidence in every region.
    if s["freeze_ready"]:
        for name, region in s["regions"].items():
            blockers = region.get("blockers", [])
            if blockers:
                errors.append(
                    f"freeze_ready=true with blockers in {name}: " + "; ".join(blockers)
                )
            nulls = list(_null_paths(region.get("selected", {})))
            if nulls:
                errors.append(
                    f"freeze_ready=true with unset targets in {name}: " + ", ".join(nulls)
                )
            grades = {k: v for k, v in region.items() if k.startswith("evidence_grade")}
            if _contains_unresolved_grade(grades):
                errors.append(f"freeze_ready=true with unresolved C/D evidence in {name}")

    # Hard invariants that can be checked from currently stored scaffold data.
    sg = s["regions"]["shoulder_girdle"]["selected"]
    for key in ("bilateral_AC_breadth_mm", "stature_conditioned_biacromial_scaffold_mm",
                "clavicle_curved_length_mm", "clavicle_SC_AC_chord_mm"):
        value = sg.get(key)
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or value <= 0
        ):
            errors.append(f"{key} must be a finite positive measurement")
    if sg["bilateral_AC_breadth_mm"] is not None:
        biac = sg["stature_conditioned_biacromial_scaffold_mm"]
        if not sg["bilateral_AC_breadth_mm"] < biac:
            errors.append("bilateral AC breadth must be less than biacromial breadth")

    if sg["clavicle_curved_length_mm"] is not None and sg["clavicle_SC_AC_chord_mm"] is not None:
        if not sg["clavicle_SC_AC_chord_mm"] < sg["clavicle_curved_length_mm"]:
            errors.append("clavicle straight chord must be shorter than curved length")

    # Spine cannot freeze while body/disc sequences remain absent.
    sp = s["regions"]["spine"]["selected"]
    if s["regions"]["spine"]["freeze_state"].startswith("FROZEN"):
        required = [
            "cervical_body_heights_mm", "cervical_disc_heights_mm",
            "thoracic_body_heights_mm", "thoracic_disc_heights_mm",
            "lumbar_body_heights_mm", "lumbar_disc_heights_mm",
            "sagittal_endplate_frame_sequence",
        ]
        for k in required:
            if sp[k] is None:
                errors.append(f"frozen spine missing {k}")

    # Preserve evidence corrections exactly. These checks intentionally encode
    # the current corrected conclusions so an older audit state cannot silently
    # return during concurrent work.
    foot = conv["region_findings"]["metatarsals"]
    if foot["grade"] != "C" or foot["state"] != "REOPEN_SOURCE_CONFLICT":
        errors.append("metatarsal source conflict was lost")

    scap = conv["region_findings"]["scapula"]
    if (
        scap["grade"] != "A"
        or scap["state"] != "CONFIRMED_TRANSVERSE_GEOMETRY_DEFECT_EXACT_3D_TARGET_OPEN"
    ):
        errors.append("corrected scapular transverse-defect state was lost")
    if "DO_NOT_FREEZE_VERTICAL_LENGTH_YET" not in scap.get("action", ""):
        errors.append("scapular exact 3D/vertical target was prematurely treated as frozen")

    # Target-selection shoulder state must agree with the evidence gate.
    sg_grade = s["regions"]["shoulder_girdle"]["evidence_grade"].get("scapula")
    if sg_grade != "A_TRANSVERSE_DEFECT_EXACT_3D_TARGET_OPEN":
        errors.append("shoulder selection does not reflect corrected scapular evidence grade")


    # Preserve both stages of source review: subtraction of the STSL distances
    # is invalid; a subsequent full-text Results paragraph reports a direct
    # distance independently. That distance is still not a transverse equality.
    if shoulder_constraint is not None:
        if "lateral_acromion_to_AC_joint_mm" in shoulder_constraint.get("inputs", {}):
            errors.append("withdrawn direct acromion-to-AC source was reintroduced")
        exact = shoulder_constraint.get("derived_constraints", {}).get("exact_AC_offset")
        direct_state = "DIRECT_3D_DISTANCE_AVAILABLE_TRANSVERSE_COMPONENT_STILL_FRAME_DEPENDENT"
        if exact not in ("UNRESOLVED_AFTER_SOURCE_CORRECTION", direct_state):
            errors.append("absolute AC offset was silently resolved after source correction")
        if exact == direct_state:
            source = (shoulder_source or {}).get("sources", {}).get("SCAPULA_AC_LATERAL_2026", {})
            if (source.get("status") != "FULL_TEXT_DIRECT_DISTANCE_VERIFIED_3D_ONLY"
                    or source.get("pmcid") != "PMC13184462"):
                errors.append("direct AC 3D constraint missing verified full-text provenance")
            measured = source.get("actual_reported_measurements_mm", {}).get("lateral_acromion_to_posterior_AC_joint")
            direct = shoulder_constraint.get("inputs", {}).get("direct_AC_to_lateral_acromion_3D_mm", {})
            selected = sg.get("direct_AC_to_lateral_acromion_3D_mm", {})
            derived = shoulder_constraint.get("derived_constraints", {}).get("direct_AC_3D_constraint", {})
            if not measured or any(direct.get(k) != measured.get(k) or selected.get(k) != measured.get(k)
                                   for k in ("mean", "sd", "range")):
                errors.append("direct AC measurement disagrees with full-text source or selection")
            if measured and any(derived.get(k + "_mm") != measured.get(k) for k in ("mean", "sd", "range")):
                errors.append("derived direct AC bound disagrees with full-text measurement")
            if derived.get("valid_relation") != "required_transverse_AC_to_lateral_acromion_component_mm <= measured_3D_distance_mm":
                errors.append("direct AC 3D distance must constrain transverse component, not equal it")

    if shoulder_source is not None:
        corrected = shoulder_source.get("sources", {}).get("SCAPULAR_LANDMARK_CADAVER_2026", {})
        if corrected.get("status") != "CORRECTED_NOT_USED_FOR_CANONICAL_AC_OFFSET":
            errors.append("corrected 2026 scapular landmark source status was lost")
        if "lateral_acromion_to_AC_joint_mm" in corrected:
            errors.append("invalid direct acromion-to-AC value reappeared in source register")

    sternum = conv["region_findings"].get("sternum")
    if not sternum or sternum.get("grade") != "C" or sternum.get("state") != "REOPEN_STATURE_METHOD_CONFLICT":
        errors.append("corrected sternum stature/method conflict state was lost")

    # Corridor file must remain explicitly non-final.
    if corr["status"] != "EVIDENCE_CORRIDORS_NOT_FINAL_TARGETS":
        errors.append("evidence corridors were promoted to final targets without selection review")

    if not s["freeze_ready"]:
        warnings.append("canonical target remains NOT FREEZE READY; Blender c001 must not be created yet")

    return {
        "selection": str(SEL.relative_to(ROOT)),
        "freeze_ready": s["freeze_ready"],
        "errors": errors,
        "warnings": warnings,
        "result": "PASS" if not errors else "FAIL",
    }


def main():
    report = validate(load(SEL), load(CONV), load(CORR), load(SHOULDER_CONSTRAINT), load(SHOULDER_SOURCE))
    print(json.dumps(report, indent=2))
    return 0 if report["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
