"""Read-only crosswalk of W8 stored edge-key geometry and observed press key values.

Combines immutable report members; never opens or modifies a Blender model.
Key value is not an isolated deformation contribution.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

W8_SHA = "2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c"
STATUS = "READ_ONLY_OBSERVED_KEY_CROSSWALK_NO_CAUSAL_OR_ANATOMICAL_APPROVAL"


def _finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def analyze(endpoint, pose):
    if endpoint.get("source_sha256") != W8_SHA or pose.get("source_sha256") != W8_SHA:
        raise ValueError("immutable W8 source SHA mismatch")
    if endpoint.get("target_edge_count") != 4 or len(endpoint.get("edges", [])) != 4:
        raise ValueError("expected exactly four pinned W8 edges")
    if pose.get("anatomical_approval") != "NOT_GRANTED" or pose.get("saved_blend") is not False or pose.get("source_unchanged") is not True:
        raise ValueError("pose evidence provenance or safety guard missing")
    if endpoint.get("anatomical_side_verified") is not False or endpoint.get("skin_deformation_validated") is not False:
        raise ValueError("endpoint report incorrectly asserts approval")
    samples = {}
    for row in pose.get("samples", []):
        idx = row.get("sample")
        if not isinstance(idx, int) or idx in samples:
            raise ValueError("duplicate or invalid pose sample")
        samples[idx] = row
    if not {0, 6, 8}.issubset(samples):
        raise ValueError("missing baseline, hotspot or final press sample")
    output = []
    seen = set()
    for edge in endpoint["edges"]:
        label = edge["ranked_report_label_NOT_anatomical_side"]
        if label in seen or not isinstance(label, str):
            raise ValueError("duplicate edge label")
        seen.add(label)
        if "_suffix_l_" in label:
            suffix = "l"
        elif "_suffix_r_" in label:
            suffix = "r"
        else:
            raise ValueError("cannot derive authored suffix")
        keys = edge["top_stored_shape_keys_by_absolute_edge_ratio_change"]
        if not isinstance(keys, list):
            raise ValueError("missing stored-key inventory")
        records = []
        for sample in (0, 6, 8):
            side = samples[sample].get("sides", {}).get(suffix)
            if not isinstance(side, dict):
                raise ValueError("missing pose side")
            actual = {}
            for key in side.get("actual_shape_key_values", []):
                name, value = key.get("name"), key.get("actual_value")
                if not isinstance(name, str) or name in actual or not _finite(value):
                    raise ValueError("invalid or duplicate observed shape key")
                actual[name] = value
            observations = []
            for key in keys:
                name = key["key"]
                ratio = key["stored_edge_length_ratio_to_Basis"]
                if not _finite(ratio) or ratio <= 0:
                    raise ValueError("invalid stored edge ratio")
                value = actual.get(name)
                observations.append({
                    "key": name,
                    "stored_edge_ratio_to_basis_NOT_pose_result": ratio,
                    "observed_value_or_null_if_not_recorded": value,
                    "observed_in_pinned_driver_report": name in actual,
                })
            records.append({
                "sample": sample,
                "measured_humerothoracic_driver_deg_NOT_ISB": side.get("humerothoracic_elevation_measured_by_pinned_driver_deg"),
                "stored_top_keys_with_observed_values": observations,
                "active_top_keys_descriptive": [x["key"] for x in observations if x["observed_value_or_null_if_not_recorded"] is not None and x["observed_value_or_null_if_not_recorded"] > 0],
                "not_recorded_top_keys": [x["key"] for x in observations if not x["observed_in_pinned_driver_report"]],
            })
        output.append({
            "edge_label_NOT_anatomical_side": label,
            "authored_suffix_NOT_anatomical_side": suffix,
            "vertex_ids": edge["rest_mesh_edge_vertex_ids"],
            "rest_edge_length_mm": edge["rest_edge_length_mm"],
            "endpoint_weight_L1_difference_NOT_tissue_strain": edge["group_weight_L1_difference_not_tissue_strain"],
            "samples": records,
        })
    return {
        "status": STATUS, "model": "W8", "source_sha256": W8_SHA,
        "edge_count": len(output), "samples_compared": [0, 6, 8],
        "anatomical_side_verified": False, "joint_axes_ISB_calibrated": False,
        "muscle_attachment_approved": False, "skin_deformation_validated": False,
        "limitations": [
            "Shape-key values are measured after the pinned shoulder driver, not isolated effects.",
            "Stored single-key geometry ratios cannot be multiplied by activation to predict posed edge lengths.",
            "Missing keys are UNKNOWN, never assumed zero.",
            "Skinning, key combinations, relative-key semantics, helper bones and collisions are not isolated.",
            "No population ROM mean is a model limit; no muscle highlighting is implemented.",
        ],
        "edges": output,
    }


def markdown(report):
    lines = ["# W8 pinned edge / observed shoulder-key crosswalk", "",
             "**READ ONLY — NO CAUSALITY OR ANATOMICAL APPROVAL.**", "",
             "| Authored edge | Sample | Measured driver deg (not ISB) | Observed active stored-top keys | Not recorded |",
             "|---|---:|---:|---|---|"]
    for edge in report["edges"]:
        for s in edge["samples"]:
            lines.append("| {} | {} | {} | {} | {} |".format(
                edge["edge_label_NOT_anatomical_side"], s["sample"],
                s["measured_humerothoracic_driver_deg_NOT_ISB"],
                ", ".join(s["active_top_keys_descriptive"]) or "(none)",
                ", ".join(s["not_recorded_top_keys"]) or "(none)"))
    lines += ["", "A key being active alongside edge stretching is not proof it caused the stretching.",
              "Missing driver records are not zeros. No model was posed or saved by this crosswalk.", ""]
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--endpoint", type=Path, required=True)
    p.add_argument("--pose", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    endpoint_raw = args.endpoint.read_bytes()
    pose_raw = args.pose.read_bytes()
    result = analyze(json.loads(endpoint_raw), json.loads(pose_raw))
    result["input_member_sha256"] = {
        "endpoint": hashlib.sha256(endpoint_raw).hexdigest(),
        "pose": hashlib.sha256(pose_raw).hexdigest(),
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "w8_elbow_corrective_crosswalk.json").write_text(json.dumps(result, indent=2) + "\n")
    (args.out / "w8_elbow_corrective_crosswalk.md").write_text(markdown(result))
    print("READ_ONLY_W8_ELBOW_CORRECTIVE_CROSSWALK", result["edge_count"], "NO_ANATOMICAL_APPROVAL")


if __name__ == "__main__":
    main()
