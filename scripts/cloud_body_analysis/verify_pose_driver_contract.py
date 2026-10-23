"""Numerically prove pinned W8 shoulder pose-keys match their measured driver angle.

No bpy; inputs are saved JSON from separate source-preserving native jobs
in the same Actions run. A correct driver formula is NOT anatomical validity.
"""
import argparse
import json
import math
from pathlib import Path

W8 = "2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c"
FAMILIES = {"HGPT_S1_SHOULDER", "HGPT_S2_FOLD", "HGPT_S3_SHAPE",
            "HGPT_S4_SCULPT", "HGPT_S5_BAKE", "HGPT_S6_RELAX", "HGPT_S7_DELT"}
ABS_TOLERANCE = 0.0001  # Numeric IO/rounding allowance, NOT anatomical tolerance.
BASELINE = {
    0: {"collapse_lt_0_1": 9, "stretch_gt_2": 1004, "self_intersecting_pairs": 11},
    6: {"collapse_lt_0_1": 110, "stretch_gt_2": 3509, "self_intersecting_pairs": 146},
    8: {"collapse_lt_0_1": 173, "stretch_gt_2": 1594, "self_intersecting_pairs": 441},
}

def finite(value):
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
        raise ValueError("nonfinite or invalid numeric value")
    return float(value)

def value_hat(e, start, angles, index):
    """Pinned r57 family hats, driven by MEASURED driver elevation."""
    e = finite(e)
    points = (finite(start),) + tuple(finite(x) for x in angles)
    if not 0 <= index < len(points)-1:
        raise ValueError("invalid key index")
    if any(hi <= lo for lo, hi in zip(points, points[1:])):
        raise ValueError("nonmonotonic actual driver angle properties")
    lo, mid = points[index:index+2]
    hi = points[index+2] if index+2 < len(points) else None
    if e <= lo:
        return 0.0
    if e <= mid:
        return (e-lo)/(mid-lo)
    if hi is None:
        return 1.0
    return max(0.0,(hi-e)/(hi-mid))

def compare(static, dynamic):
    if (static.get("model") != "W8" or static.get("source_sha256") != W8
        or static.get("original_source_unchanged") is not True
        or static.get("status") != "READ_ONLY_ANGULAR_ACTIVATION_CONTRACT_NOT_APPLIED_TO_POSE"):
        raise ValueError("unverified W8 static driver reference")
    if (dynamic.get("model") != "W8" or dynamic.get("source_sha256") != W8
        or dynamic.get("source_unchanged") is not True
        or dynamic.get("saved_blend") is not False
        or dynamic.get("anatomical_approval") != "NOT_GRANTED"
        or dynamic.get("quality_approval") != "NOT_GRANTED"
        or dynamic.get("status") != "READ_ONLY_IN_MEMORY_POSE_STATE_ANATOMY_NOT_APPROVED"):
        raise ValueError("unverified or promoted W8 actual pose")
    families = {(r["family"],r["side_suffix"]):r for r in static["family_records"]
                if r["family"] in FAMILIES and r["side_suffix"] in ("l","r")}
    if len(families) != 14:
        raise ValueError("seven shoulder corrective families required on both sides")
    if any(not f.get("safe_to_evaluate_rule") or f.get("measurement") != "humerothoracic_elevation"
           or len(f["keys"]) != len(f["angle_properties_deg"])
           for f in families.values()):
        raise ValueError("incomplete shoulder family angles/key contract")
    samples = dynamic.get("samples")
    if not isinstance(samples, list) or len(samples) != 9 or [s.get("sample") for s in samples] != list(range(9)):
        raise ValueError("missing or unordered 9 native W8 samples")
    deviations, trials = [], []
    for sample in samples:
        index=sample["sample"]
        target=finite(sample["authored_press_ht_target_deg_NOT_measured"])
        for side in ("l","r"):
            row=sample["sides"][side]
            measured=finite(row["humerothoracic_elevation_measured_by_pinned_driver_deg"])
            observed={entry["name"]:finite(entry["actual_value"])
                      for entry in row["actual_shape_key_values"]}
            if len(observed)!=len(row["actual_shape_key_values"]):
                raise ValueError("duplicate actual shape-key names")
            trials.append({"sample":index,"side_suffix":side,"target_deg":target,
                           "driver_measured_deg":measured,
                           "target_minus_driver_deg":round(target-measured,5)})
            for (name,s), family in families.items():
                if s != side:
                    continue
                for n,key in enumerate(family["keys"]):
                    if key["name"] not in observed:
                        raise ValueError("missing actual key "+key["name"])
                    pred=value_hat(measured,family["effective_start_deg"],family["angle_properties_deg"],n)
                    actual=observed[key["name"]]
                    deviations.append({"sample":index,"side_suffix":side,"key":key["name"],
                                       "predicted":round(pred,6),"actual":round(actual,6),
                                       "absolute_difference":abs(pred-actual)})
    if len(deviations) != 378:
        raise ValueError("incomplete 9 frames x 2 sides x 21 keys")
    max_err=max(v["absolute_difference"] for v in deviations)
    if max_err>ABS_TOLERANCE:
        worst=max(deviations,key=lambda r:r["absolute_difference"])
        raise ValueError(f"Actual driver hats do NOT match measured elevation; worst {worst}")
    for frame, expected in BASELINE.items():
        actual=samples[frame]["actual_native_deformation_metrics"]
        if any(actual.get(k)!=v for k,v in expected.items()):
            raise ValueError("W8 pinned failing deformation counts changed at sample "+str(frame))
    output={
        "status":"PINNED_W8_DRIVER_MATH_REPRODUCED_ONLY_HUMAN_MOTION_NOT_APPROVED",
        "model":"W8","source_sha256":W8,
        "actual_compared_shape_key_values":len(deviations),
        "nominal_family_count":len(FAMILIES),
        "actual_absolutemax_key_residual":round(max_err,9),
        "numeric_residual_tolerance_not_anatomical":ABS_TOLERANCE,
        "all_measured_driver_hats_match":True,
        "note":"Measured r57 vector elevation, not intended target, controls key interpolation.",
        "frame_target_vs_measured":trials,
        "failing_baseline_metrics_unchanged":True,
        "anatomical_side_mapping_verified":False,
        "joint_coordinate_ISB_verified":False,
        "source_reconstruction_approved":False,
        "shoulder_surface_deformation_approved":False,
        "no_original_model_saved":True,
        "limitations":[
            "A numerically correct shape-key hat can still deform the anatomy incorrectly",
            "Does not certify clinical ranges of motion, muscle force or human appearance",
            "Checks S1-S7 only; C1 extension uses a DIFFERENT driver, not shoulder elevation",
            "Does not establish why project target differs from measured HT elevation",
            "Only current immutable W8 and its known-failing press are pinned; do not compare model revision by raw triangle counts",
        ],
    }
    return output

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--static",type=Path,required=True)
    p.add_argument("--actual",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=compare(json.loads(a.static.read_text()),json.loads(a.actual.read_text()))
    a.out.mkdir(parents=True,exist_ok=False)
    (a.out/"w8_driver_math_consistency.json").write_text(json.dumps(result,indent=2)+"\n")
    print("PINNED_W8_DRIVER_MATH_VERIFIED",result["actual_compared_shape_key_values"],
          "MAX_ABS_RESIDUAL",result["actual_absolutemax_key_residual"],
          "ANATOMY_NOT_APPROVED",flush=True)

if __name__=="__main__":
    main()
