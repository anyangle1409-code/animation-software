"""Read-only W8 nine-frame press failure timeline from an observed Blender report.

Correlates recorded per-frame driver states with aggregate quality metrics only.
No mesh edits, anatomical axis claims, causal attribution, or exercise approval.
"""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path

W8_SOURCE_SHA256 = "2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c"
PINNED_DRIVER_REV = "025d5f28fa7eba2064fba565b1c9b60119cdd2cb"
COUNT_METRICS = ("collapse_lt_0_1", "stretch_gt_2", "self_intersecting_pairs")
VOLUME_METRIC = "body_volume_change_pct"
KEY_RE = re.compile(r"^HGPT_(C1_ARMTRUNK|S1_SHOULDER|S3_SHAPE|S5_BAKE|S7_DELT)_([lr])_(-?\d+)$")


def finite_number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{label}: expected finite numeric value")
    return float(value)


def validated_samples(doc):
    if (doc.get("model") != "W8" or doc.get("source_sha256") != W8_SOURCE_SHA256
        or doc.get("pinned_r57_source_commit") != PINNED_DRIVER_REV
        or doc.get("status") != "READ_ONLY_IN_MEMORY_POSE_STATE_ANATOMY_NOT_APPROVED"
        or doc.get("source_unchanged") is not True or doc.get("saved_blend") is not False
        or doc.get("rest_bone_signature_unchanged") is not True
        or doc.get("anatomical_approval") != "NOT_GRANTED"
        or doc.get("quality_approval") != "NOT_GRANTED"
        or doc.get("model_is_reconstruction_not_approved_original") is not True
        or doc.get("key_values_measured_after_actual_post_pose_driver_call") is not True):
        raise ValueError("source/model/approval provenance mismatch; refuse analysis")
    samples = doc.get("samples")
    if not isinstance(samples, list) or len(samples) != 9:
        raise ValueError("expected exactly nine native press samples")
    names_by_side = {}
    rows = []
    for index, sample in enumerate(samples):
        if type(sample.get("sample")) is not int or sample["sample"] != index:
            raise ValueError("missing/reordered sample index")
        t = finite_number(sample.get("t"), "t")
        if abs(t-index/8) > 1e-7:
            raise ValueError("unexpected sample time")
        target = finite_number(sample.get("authored_press_ht_target_deg_NOT_measured"), "authored target")
        sides = sample.get("sides")
        if not isinstance(sides, dict) or set(sides) != {"l", "r"}:
            raise ValueError("both authored suffixes required; anatomical side unknown")
        metrics = sample.get("actual_native_deformation_metrics")
        if not isinstance(metrics, dict) or set(metrics) != set(COUNT_METRICS) | {VOLUME_METRIC}:
            raise ValueError("native deformation metrics incomplete")
        for key in COUNT_METRICS:
            if type(metrics[key]) is not int or metrics[key] < 0:
                raise ValueError("invalid nonnegative count metric " + key)
        finite_number(metrics[VOLUME_METRIC], VOLUME_METRIC)
        side_rows = {}
        for suffix in ("l", "r"):
            state = sides[suffix]
            angle = finite_number(state.get("humerothoracic_elevation_measured_by_pinned_driver_deg"), "driver angle")
            offset = finite_number(state.get("target_minus_driver_measurement_deg"), "driver offset")
            if abs((target-angle)-offset) > 0.00005:
                raise ValueError("target/driver difference inconsistent")
            cap = state.get("cap_helper_present")
            axilla = state.get("axilla_helper_present")
            if type(cap) is not bool or type(axilla) is not bool:
                raise ValueError("helper presence must be explicit boolean")
            cap_angle = state.get("cap_local_delta_angle_deg_not_absolute")
            axilla_angle = state.get("axilla_local_delta_angle_deg_not_absolute")
            if cap:
                finite_number(cap_angle, "cap local angle")
            elif cap_angle is not None:
                raise ValueError("absent cap cannot report local angle")
            if axilla:
                finite_number(axilla_angle, "axilla local angle")
            elif axilla_angle is not None:
                raise ValueError("absent axilla cannot report local angle")
            keys = state.get("actual_shape_key_values")
            if not isinstance(keys, list) or not keys:
                raise ValueError("missing actual shape-key observations")
            values = {}
            for item in keys:
                name = item.get("name")
                match = KEY_RE.fullmatch(name) if isinstance(name, str) else None
                if not match or match.group(2) != suffix or name in values:
                    raise ValueError("invalid, wrong-suffix, or duplicate key")
                value = finite_number(item.get("actual_value"), "shape key")
                if value < -1e-5 or value > 1.00001:
                    raise ValueError("out-of-range shape key")
                values[name] = value
            if suffix in names_by_side and set(values) != names_by_side[suffix]:
                raise ValueError("shape-key inventory changed between frames")
            names_by_side[suffix] = set(values)
            active = {}
            for family in ("C1_ARMTRUNK", "S1_SHOULDER", "S3_SHAPE", "S5_BAKE", "S7_DELT"):
                fam = {k: v for k, v in values.items() if k.startswith("HGPT_" + family + "_")}
                if not fam:
                    raise ValueError("missing key family " + family)
                active[family] = {"active_key_count": sum(v > 1e-6 for v in fam.values()),
                                  "weight_sum": round(sum(fam.values()), 6),
                                  "largest_key": max(fam, key=fam.get),
                                  "largest_weight": max(fam.values())}
            side_rows[suffix] = {"driver_measured_ht_deg_NOT_ISB": angle,
                                 "authored_minus_measured_deg": offset,
                                 "cap_helper_present": cap,
                                 "cap_local_delta_deg_NOT_absolute": cap_angle,
                                 "axilla_helper_present": axilla,
                                 "axilla_local_delta_deg_NOT_absolute": axilla_angle,
                                 "families": active}
        rows.append({"sample": index, "t": t, "authored_target_deg_NOT_measured": target,
                     "native_metrics": dict(metrics), "suffixes_NOT_anatomical_sides": side_rows,
                     "measured_driver_angle_suffix_difference_abs_deg": abs(
                         side_rows["l"]["driver_measured_ht_deg_NOT_ISB"]-
                         side_rows["r"]["driver_measured_ht_deg_NOT_ISB"])})
    return rows


def summarize(doc, *, input_sha256):
    rows = validated_samples(doc)
    metric_summary = {}
    for key in COUNT_METRICS:
        vals = [row["native_metrics"][key] for row in rows]
        peak = max(vals)
        jumps = [vals[i]-vals[i-1] for i in range(1, 9)]
        metric_summary[key] = {
            "baseline_sample0": vals[0], "final_sample8": vals[-1],
            "peak": peak, "peak_samples": [i for i, v in enumerate(vals) if v == peak],
            "peak_minus_baseline_count_difference_NOT_new_triangle_IDs": peak-vals[0],
            "largest_positive_adjacent_count_jump": max(jumps),
            "adjacent_jump_samples": [i for i, v in enumerate(jumps, start=1) if v == max(jumps)],
        }
    vol = [row["native_metrics"][VOLUME_METRIC] for row in rows]
    return {
        "status": "OBSERVED_W8_PRESS_TIMELINE_ONLY_EXISTING_DEFORMATION_FAILS",
        "input_member_sha256": input_sha256, "model": "W8",
        "source_blend_sha256": W8_SOURCE_SHA256,
        "driver_code_revision": PINNED_DRIVER_REV,
        "observed_sample_count": 9,
        "metrics": metric_summary,
        "volume_change_pct_descriptive": {"baseline": vol[0], "final": vol[-1],
                                          "minimum": min(vol), "maximum": max(vol)},
        "max_driver_angle_suffix_difference_abs_deg": max(
            row["measured_driver_angle_suffix_difference_abs_deg"] for row in rows),
        "axilla_helper_present_in_any_observed_frame": any(
            row["suffixes_NOT_anatomical_sides"][s]["axilla_helper_present"]
            for row in rows for s in ("l", "r")),
        "cap_helper_present_in_every_observed_frame": all(
            row["suffixes_NOT_anatomical_sides"][s]["cap_helper_present"]
            for row in rows for s in ("l", "r")),
        "observed_frames": rows,
        "generic_motion_tests_executed": 0,
        "anatomical_landmarks_calibrated": 0,
        "isb_joint_frames_approved": False,
        "skin_deformation_approved": False,
        "exercise_approved": False,
        "muscle_attachments_approved": False,
        "clinical_rom_means_used_as_limits": False,
        "muscle_highlighting_implemented": False,
        "limitations": [
            "Actual Blender nine-frame W8 reconstructed press evidence, not invented motion or ISB coordinates.",
            "Metrics are whole-body aggregate counts; no regional attribution or new triangle IDs inferred.",
            "Concurrent shape-key/driver/defect changes establish no causality or repair.",
            "Local cap helper delta is not absolute anatomical clavicle/scapula/GH rotation.",
            "Suffix l/r is not independently established anatomical left/right.",
            "Only nine sampled press states; no return trajectory, forearm pronation, or generic 19-test execution.",
            "Shoulder press, squat and grip benchmark acceptance remains FAILED/BLOCKED.",
        ],
    }


def markdown(report):
    lines = ["# W8 observed shoulder-press deformation timeline (read-only)", "",
             "**Existing native quality failures persist. No anatomical joint frames or skin approved.**", "",
             f"Source W8 SHA256: `{report['source_blend_sha256']}`; pose JSON SHA256: `{report['input_member_sha256']}`.",
             "Nine actual in-memory Blender samples; measured driver angles are NOT ISB GH/HT calibration.", "",
             "| Sample | Driver HT suffix l (°) | Cap local delta suffix l (°) | Stretch flags | Collapse flags | Intersection pairs |",
             "|---:|---:|---:|---:|---:|---:|"]
    for row in report["observed_frames"]:
        l = row["suffixes_NOT_anatomical_sides"]["l"]
        m = row["native_metrics"]
        lines.append(f"| {row['sample']} | {l['driver_measured_ht_deg_NOT_ISB']:.3f} | "
                     f"{l['cap_local_delta_deg_NOT_absolute']:.3f} | {m['stretch_gt_2']} | "
                     f"{m['collapse_lt_0_1']} | {m['self_intersecting_pairs']} |")
    lines += ["", "**Recorded maxima (not anatomy thresholds):**"]
    for key, row in report["metrics"].items():
        lines.append(f"- `{key}`: peak {row['peak']} at sample(s) {row['peak_samples']}; "
                     f"baseline {row['baseline_sample0']}; final {row['final_sample8']}.")
    lines += ["", "Axilla helper present in any sampled frame: " + str(report["axilla_helper_present_in_any_observed_frame"]),
              "Cap helper present in all sampled frames: " + str(report["cap_helper_present_in_every_observed_frame"]),
              "", "**No causality:** changes in key weights and aggregate failures co-occur, but the data do not isolate any driver, muscle, or tissue region.",
              "No actual skin repair, anatomical side, segment axis, new movement trial, muscle attachment, ROM clamp, or highlighting was implemented.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--actual", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    raw = args.actual.read_bytes()
    report = summarize(json.loads(raw), input_sha256=hashlib.sha256(raw).hexdigest())
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "w8_press_deformation_timeline.json").write_text(json.dumps(report, indent=2) + "\n")
    (args.out / "w8_press_deformation_timeline.md").write_text(markdown(report))
    print(report["status"], report["observed_sample_count"], "observed frames")


if __name__ == "__main__":
    main()
