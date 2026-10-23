"""Metadata-only reconstruction of pinned shoulder corrective activation rules.

Mirrors the piecewise-linear elevation/extension activation *math*, but never
poses a rig, calls drive(), changes shape-key values or saves a .blend.
Rule source: scripts/original_v1_review_candidate_drives.py at 025d5f28.
"""
import math

# (key-prefix, rig-angle-property prefix, nominal start, measured quantity)
FAMILIES = (
    ("HGPT_S1_SHOULDER_", "hgpt_s1_angles", 90.0, "humerothoracic_elevation"),
    ("HGPT_S2_FOLD_", "hgpt_s2_angles", 90.0, "humerothoracic_elevation"),
    ("HGPT_S3_SHAPE_", "hgpt_s3_angles", 20.0, "humerothoracic_elevation"),
    ("HGPT_S4_SCULPT_", "hgpt_s4_angles", 60.0, "humerothoracic_elevation"),
    ("HGPT_S5_BAKE_", "hgpt_s5_angles", 60.0, "humerothoracic_elevation"),
    ("HGPT_S6_RELAX_", "hgpt_s6_angles", 120.0, "humerothoracic_elevation"),
    ("HGPT_S7_DELT_", "hgpt_s7_angles", 130.0, "humerothoracic_elevation"),
    ("HGPT_C1_ARMTRUNK_", "hgpt_c1_angles", 18.0, "shoulder_extension"),
)
SAMPLE_DEGREES = (0, 20, 60, 90, 105, 120, 130, 136, 145, 156, 160, 166, 172, 180)

def hat(e, start, angles, index):
    """Same equation as drive_s1()/drive_c1() in the pinned source, for valid monotone points."""
    pts = (start,) + tuple(angles)
    lo, mid = pts[index:index + 2]
    hi = pts[index + 2] if index + 2 < len(pts) else None
    if e <= lo:
        return 0.0
    if e <= mid:
        return (e - lo) / (mid - lo)
    if hi is None:
        return 1.0
    return max(0.0, (hi - e) / (hi - mid))

def finite_number(value, what):
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(what + " is nonfinite")
    return out

def inspect(rig, body):
    key_tree = body.data.shape_keys
    if key_tree is None:
        raise ValueError("model has no shape-key data")
    blocks = key_tree.key_blocks
    names = {kb.name for kb in blocks}
    if len(names) != len(blocks):
        raise ValueError("duplicate shape-key names")

    families = []
    for prefix, prop, default_start, measurement in FAMILIES:
        if measurement == "shoulder_extension":
            start = default_start  # pinned drive_c1() uses fixed C1_START
            override = False
        else:
            start = finite_number(rig.get(prop + "_start", default_start), prop + "_start")
            override = (prop + "_start") in rig
        if not 0 <= start <= 180:
            raise ValueError(prop + ": start out of expected angle range")
        for side in ("l", "r"):
            candidates = []
            for kb in blocks:
                if not kb.name.startswith(prefix + side + "_"):
                    continue
                try:
                    suffix_angle = int(kb.name.rsplit("_", 1)[1])
                except (IndexError, ValueError) as e:
                    raise ValueError("malformed shoulder key name " + kb.name) from e
                candidates.append((suffix_angle, kb))
            candidates.sort(key=lambda p: (p[0], p[1].name))
            prop_name = prop + "_" + side
            property_present = prop_name in rig
            raw = list(rig[prop_name]) if property_present else []
            angles = [finite_number(v, prop_name) for v in raw]
            is_strict_increase = (len(angles) > 0
                                  and all(start < a <= 180 for a in angles)
                                  and all(a < b for a, b in zip(angles, angles[1:])))
            counts_match = len(angles) == len(candidates)
            configured = bool(candidates) and property_present
            evaluable = configured and is_strict_increase and counts_match
            warnings = []
            if candidates and not property_present:
                warnings.append("SHAPE_KEYS_WITHOUT_RIG_ANGLE_PROPERTY")
            if property_present and not candidates:
                warnings.append("RIG_ANGLE_PROPERTY_WITHOUT_SHAPE_KEYS")
            if configured and not counts_match:
                warnings.append("KEY_COUNT_ANGLE_COUNT_DISAGREEMENT")
            if configured and not is_strict_increase:
                warnings.append("NONMONOTONE_OR_OUT_OF_RANGE_ANGLES")
            if configured and [n for n, _ in candidates] != angles:
                warnings.append("KEY_NAME_DEGREES_DIFFER_FROM_PROPERTY_ANGLES")
            key_records = []
            for i, (suffix_angle, key) in enumerate(candidates):
                saved_value = finite_number(key.value, key.name + ".value")
                item = {
                    "name": key.name, "suffix_angle_deg": suffix_angle,
                    "saved_key_value": round(saved_value, 6),
                }
                if evaluable:
                    item["predicted_values_at_hypothetical_degrees"] = {
                        str(e): round(hat(e, start, angles, i), 6) for e in SAMPLE_DEGREES
                    }
                key_records.append(item)
            families.append({
                "family": prefix.rstrip("_"), "side_suffix": side,
                "measurement": measurement,
                "rig_angles_property": prop_name,
                "property_present": property_present,
                "nominal_start_deg": default_start,
                "effective_start_deg": start,
                "start_override_present": override,
                "angle_properties_deg": angles,
                "angle_property_count_matches_key_count": counts_match,
                "safe_to_evaluate_rule": evaluable,
                "warnings": warnings,
                "keys": key_records,
            })
    unclassified = sorted(names - {
        key["name"] for family in families for key in family["keys"]
    })
    return {
        "status": "READ_ONLY_ANGULAR_ACTIVATION_CONTRACT_NOT_APPLIED_TO_POSE",
        "method": "Algebraic reproduction of pinned drive_s1()/drive_c1() hats",
        "pinned_source_commit": "025d5f28fa7eba2064fba565b1c9b60119cdd2cb",
        "shape_key_count": len(blocks),
        "family_records": families,
        "unclassified_key_names": unclassified,
        "limitations": [
            "These sampled degrees are HYPOTHETICAL, not measured joint angles from shoulder-press frames",
            "This report does not call drive(), move bones, animate the body or activate a shape key",
            "As-loaded key values are not the values applied during prior movement benchmarks",
            "Rule activation does not establish mesh deformation causation or anatomical correctness",
            "Side suffixes are not independently certified anatomical laterality",
        ],
    }
