import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SEL = ROOT / "ORIGINAL_V1_WORK/anatomy/canonical_target_selection_v1.json"
CONV = ROOT / "ORIGINAL_V1_WORK/anatomy/canonical_evidence_convergence_v1.json"
CORR = ROOT / "ORIGINAL_V1_WORK/anatomy/canonical_target_corridors_v1.json"

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


def main():
    s, conv, corr = load(SEL), load(CONV), load(CORR)
    errors = []
    warnings = []

    if set(s["regions"]) != REQUIRED_REGIONS:
        errors.append(f"region set mismatch: {set(s['regions']) ^ REQUIRED_REGIONS}")

    if s["freeze_ready"]:
        unresolved = [
            name for name, region in s["regions"].items()
            if "NOT_SELECTED" in region["freeze_state"]
            or "GEOMETRY_MODEL_REQUIRED" in region["freeze_state"]
            or region["freeze_state"] == "LOW_PRIORITY_NOT_SELECTED"
        ]
        if unresolved:
            errors.append("freeze_ready=true with unresolved regions: " + ", ".join(unresolved))

    # C/D evidence may be tracked, but exact numeric target values must not be silently frozen.
    def walk(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                yield from walk(v, f"{path}.{k}" if path else k)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                yield from walk(v, f"{path}[{i}]")
        else:
            yield path, obj

    # Hard invariants that can be checked from currently stored scaffold data.
    sg = s["regions"]["shoulder_girdle"]["selected"]
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

    # Preserve the explicit evidence corrections.
    foot = conv["region_findings"]["metatarsals"]
    if foot["grade"] != "C" or foot["state"] != "REOPEN_SOURCE_CONFLICT":
        errors.append("metatarsal source conflict was lost")
    scap = conv["region_findings"]["scapula"]
    if scap["grade"] != "C":
        errors.append("scapular method conflict was lost")

    # Corridor file must remain explicitly non-final.
    if corr["status"] != "EVIDENCE_CORRIDORS_NOT_FINAL_TARGETS":
        errors.append("evidence corridors were promoted to final targets without selection review")

    if not s["freeze_ready"]:
        warnings.append("canonical target remains NOT FREEZE READY; Blender c001 must not be created yet")

    report = {
        "selection": str(SEL.relative_to(ROOT)),
        "freeze_ready": s["freeze_ready"],
        "errors": errors,
        "warnings": warnings,
        "result": "PASS" if not errors else "FAIL",
    }
    print(json.dumps(report, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
