"""READ ONLY: observe the frozen r57 W8 authored forearm-rotation path.

The report describes one authored forearm control, two twist helpers and their
evaluated skin proxy. It does not establish radius/ulna frames, ISB joint
coordinates, anatomical laterality, tissue safety or movement approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

W8_SHA256 = "2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c"
R57_SHA = "025d5f28fa7eba2064fba565b1c9b60119cdd2cb"
EXPECTED_MODES = {
    "forearm": "YXZ",
    "forearm_tw0": "QUATERNION",
    "forearm_tw1": "QUATERNION",
    "hand": "XYZ",
}
REQUIRED_LIMITATIONS = (
    "Authored suffixes l/r are rig labels, not independently verified anatomical laterality",
    "A single forearm control and two twist helpers do not establish independent radius and ulna motion",
    "Local control rotations are not signed ISB joint coordinates or anatomical range of motion",
    "Population movement means describe the frozen authored target and are not hard joint limits",
    "Evaluated forearm slice-radius ratios are geometric skinning proxies, not tissue safety or muscle continuity",
    "The plain frozen benchmark clears shape keys and its slice-radius metric is not driven corrective-skin evidence",
    "The path ends at authored supination and does not test return to neutral",
)


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _number(value):
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value)
    except (OverflowError, TypeError, ValueError):
        return False


def _finite(value):
    if not _number(value):
        raise ValueError("finite numerical value required")
    return float(value)


def _vector(value, size):
    if not isinstance(value, (list, tuple)) or len(value) != size:
        raise ValueError(f"{size}D vector required")
    return [_finite(component) for component in value]


def smooth(t):
    value = max(0.0, min(1.0, _finite(t)))
    return value * value * (3.0 - 2.0 * value)


def authored_target_deg(t, pronation_mean, supination_mean):
    """Frozen signed target convention; diagnostic only, never an ISB angle."""
    t = _finite(t)
    pronation_mean = _finite(pronation_mean)
    supination_mean = _finite(supination_mean)
    if pronation_mean < 0.0 or supination_mean < 0.0:
        raise ValueError("nonnegative population means required")
    if t <= 0.5:
        return pronation_mean * smooth(2.0 * t)
    return pronation_mean + (-supination_mean - pronation_mean) * smooth(2.0 * t - 1.0)


def _normalized_quaternion(value):
    q = _vector(value, 4)
    norm = math.hypot(*q)
    if not math.isfinite(norm) or norm <= 1e-12:
        raise ValueError("nonzero quaternion required")
    return [component / norm for component in q]


def verify_r57_root(root):
    """Fail closed unless the supplied checkout is exactly the frozen revision."""
    try:
        completed = subprocess.run(
            ["git", "-C", str(Path(root).resolve()), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValueError("Unable to verify pinned r57 revision") from exc
    if completed.stdout.strip() != R57_SHA:
        raise ValueError("Pinned r57 revision mismatch")


def quaternion_distance_deg(a, b):
    """Shortest unsigned orientation distance, invariant to q versus -q."""
    qa, qb = _normalized_quaternion(a), _normalized_quaternion(b)
    dot = min(1.0, abs(sum(x * y for x, y in zip(qa, qb))))
    return math.degrees(2.0 * math.acos(dot))


def quaternion_angle_deg(value):
    return quaternion_distance_deg([1.0, 0.0, 0.0, 0.0], value)


def control_record(pose_bones, rig_world, name):
    bone = pose_bones.get(name)
    if bone is None:
        return {"control_present": False}
    quaternion = bone.matrix_basis.to_quaternion()
    q = [_finite(component) for component in quaternion]
    return {
        "control_present": True,
        "pose_rotation_mode": bone.rotation_mode,
        "matrix_basis_quaternion_wxyz": q,
        "local_delta_angle_deg_not_anatomical": quaternion_angle_deg(q),
        "head_world_m_not_anatomical_joint_centre": [
            _finite(component) for component in rig_world @ bone.head],
        "tail_world_m": [_finite(component) for component in rig_world @ bone.tail],
    }


def _valid_control(record, expected_mode):
    if not isinstance(record, dict) or set(record) != {
            "control_present", "pose_rotation_mode",
            "matrix_basis_quaternion_wxyz",
            "local_delta_angle_deg_not_anatomical",
            "head_world_m_not_anatomical_joint_centre", "tail_world_m"}:
        return False, False
    try:
        q = _normalized_quaternion(record["matrix_basis_quaternion_wxyz"])
        angle = _finite(record["local_delta_angle_deg_not_anatomical"])
        _vector(record["head_world_m_not_anatomical_joint_centre"], 3)
        _vector(record["tail_world_m"], 3)
    except (TypeError, ValueError):
        return False, False
    valid = (record["control_present"] is True
             and record["pose_rotation_mode"] == expected_mode
             and 0.0 <= angle <= 180.000001)
    consistent = math.isclose(angle, quaternion_angle_deg(q), abs_tol=1e-6)
    return valid, consistent


def validate_report(data):
    errors = []
    if not isinstance(data, dict):
        return ["invalid evidence scope"]
    if (data.get("status") !=
            "READ_ONLY_AUTHORED_FOREARM_CONTROL_PATH_ANATOMY_NOT_APPROVED"
            or data.get("evidence_kind") != "NATIVE_PINNED_MODEL_OBSERVATION"
            or data.get("synthetic_test_fixture") is not False
            or data.get("model") != "W8"
            or data.get("source_sha256") != W8_SHA256
            or data.get("pinned_r57_source_commit") != R57_SHA
            or data.get("source_unchanged") is not True
            or data.get("saved_blend") is not False
            or data.get("rest_bone_signature_unchanged") is not True
            or data.get("authored_suffixes_not_anatomical_laterality") != ["l", "r"]
            or data.get("separate_radius_ulna_controls_observed") is not False
            or data.get("anatomical_joint_coordinate_system_verified") is not False
            or data.get("pronation_supination_approved") is not False
            or data.get("return_to_neutral_tested") is not False):
        errors.append("invalid evidence scope")
    limitations = data.get("limitations")
    if (not isinstance(limitations, list)
            or any(item not in limitations for item in REQUIRED_LIMITATIONS)):
        errors.append("missing required limitations")
    means = data.get("population_means_deg_not_limits")
    if (not isinstance(means, dict)
            or set(means) != {"forearm_pronation", "forearm_supination"}
            or any(not _number(means.get(key)) or means[key] < 0.0 for key in means)):
        errors.append("invalid population means")
        means = None
    samples = data.get("samples")
    if (not isinstance(samples, list) or len(samples) != 9
            or any(not isinstance(row, dict) for row in samples)
            or any(type(row.get("sample")) is not int
                   for row in samples if isinstance(row, dict))
            or [row.get("sample") for row in samples if isinstance(row, dict)] != list(range(9))):
        errors.append("samples 0 through 8 required")
        if not isinstance(samples, list):
            return errors
    for index, row in enumerate(samples[:9]):
        if not isinstance(row, dict):
            errors.append("invalid sample")
            continue
        t = row.get("t")
        if not _number(t) or not math.isclose(t, index / 8.0, abs_tol=1e-12):
            errors.append("invalid sample parameter")
        target = row.get("authored_target_deg_not_isb")
        if means is not None and _number(t):
            expected = authored_target_deg(t, means["forearm_pronation"],
                                           means["forearm_supination"])
            if not _number(target) or not math.isclose(target, expected, abs_tol=1e-7):
                errors.append("authored target drift")
        elif not _number(target):
            errors.append("authored target drift")
        angles = row.get("benchmark_angles_deg_population_means_not_limits")
        if (not isinstance(angles, dict)
                or set(angles) != {"elbow_flexion", "forearm_pronation",
                                   "forearm_supination"}
                or any(not _number(value) for value in angles.values())
                or not math.isclose(angles.get("elbow_flexion", -1.0), 90.0,
                                    abs_tol=0.011)
                or not _number(target)
                or not math.isclose(angles.get("forearm_pronation", -1.0),
                                    max(target, 0.0), abs_tol=0.011)
                or not math.isclose(angles.get("forearm_supination", -1.0),
                                    max(-target, 0.0), abs_tol=0.011)):
            errors.append("benchmark angle mismatch")
        skin = row.get("evaluated_forearm_skin")
        if (not isinstance(skin, dict)
                or set(skin) != {"minimum_slice_radius_ratio_l",
                                 "minimum_slice_radius_ratio_r",
                                 "anatomical_tissue_safety_claimed"}
                or skin.get("anatomical_tissue_safety_claimed") is not False
                or any(not _number(skin.get(f"minimum_slice_radius_ratio_{side}"))
                       or skin[f"minimum_slice_radius_ratio_{side}"] <= 0.0
                       for side in ("l", "r"))):
            errors.append("invalid evaluated forearm skin observation")
        sides = row.get("sides")
        if not isinstance(sides, dict) or set(sides) != {"l", "r"}:
            errors.append("both authored suffixes required")
            continue
        for side in ("l", "r"):
            controls = sides.get(side)
            if not isinstance(controls, dict) or set(controls) != set(EXPECTED_MODES):
                errors.append("invalid control observation")
                continue
            for name, mode in EXPECTED_MODES.items():
                valid, consistent = _valid_control(controls.get(name), mode)
                if not valid:
                    errors.append("invalid control observation")
                elif not consistent:
                    errors.append("control quaternion/angle mismatch")
    return errors


def markdown(data):
    errors = validate_report(data)
    if errors:
        raise ValueError("invalid forearm pose report: " + "; ".join(errors))
    lines = [
        "# W8 authored forearm-control path — native read-only observation", "",
        "This is native pinned-model evidence for the frozen nine-frame authored path. "
        "It is not an anatomical pronation/supination validation.", "",
        "| Sample | t | authored signed target° (not ISB) | pronation field° | supination field° | min slice ratio l/r |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in data["samples"]:
        angles = row["benchmark_angles_deg_population_means_not_limits"]
        skin = row["evaluated_forearm_skin"]
        lines.append(
            f"| {row['sample']} | {row['t']:.3f} | {row['authored_target_deg_not_isb']:.5f} | "
            f"{angles['forearm_pronation']:.2f} | {angles['forearm_supination']:.2f} | "
            f"{skin['minimum_slice_radius_ratio_l']:.4f} / "
            f"{skin['minimum_slice_radius_ratio_r']:.4f} |")
    lines += ["", "## Local control rotation magnitudes (not anatomical angles)", "",
              "| Sample | Suffix | forearm° | twist 0° | twist 1° | hand° |",
              "|---:|:---:|---:|---:|---:|---:|"]
    for row in data["samples"]:
        for side in ("l", "r"):
            controls = row["sides"][side]
            lines.append(
                f"| {row['sample']} | {side} | "
                f"{controls['forearm']['local_delta_angle_deg_not_anatomical']:.5f} | "
                f"{controls['forearm_tw0']['local_delta_angle_deg_not_anatomical']:.5f} | "
                f"{controls['forearm_tw1']['local_delta_angle_deg_not_anatomical']:.5f} | "
                f"{controls['hand']['local_delta_angle_deg_not_anatomical']:.5f} |")
    lines += ["", "## Required limitations", ""]
    lines.extend(f"- {item}." for item in data["limitations"])
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--r57-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    sources = list(args.source_dir.rglob("*.blend"))
    if len(sources) != 1:
        raise ValueError("Exactly one preserved W8 blend expected, got " + str(sources))
    source = sources[0].resolve()
    if digest(source) != W8_SHA256:
        raise ValueError("W8 source hash mismatch")

    root = args.r57_root.resolve()
    verify_r57_root(root)
    sys.path[:0] = [str(root / "scripts"), str(root / "scripts" / "anatomy_fit"),
                    str(Path(__file__).resolve().parents[1] / "recovery_diagnostics")]
    import bpy
    import diagnose_candidates_blender as adapter
    import build_original_movement_benchmarks_blender as bench
    import build_functional_shoulder_correction_blender as correction
    import original_v1_review_candidate_drives as drives
    import original_v1_press_extension as press_extension

    if adapter.candidate_name(digest(source)) != "W8":
        raise ValueError("W8 registry mismatch")
    bpy.context.preferences.filepaths.use_scripts_auto_execute = False
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
    body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
    rig = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
    before = adapter.rest_signature(rig, body)
    result = adapter.loaded_result(bpy, correction, drives)
    press_extension.install()
    if "hgpt_cap_fraction_ramp" in rig or press_extension._PATH["name"] != "v4":
        raise ValueError("Pinned benchmark press variant changed")
    if len(rig.data.bones) != 77:
        raise ValueError("Native armature count changed")

    original_build = correction.build_corrected_scene
    correction.build_corrected_scene = lambda: result
    captures = []

    def capture(loaded):
        bones = loaded["runtime"].pose.bones
        captures.append({
            "sides": {
                side: {
                    name: control_record(bones, rig.matrix_world, f"{name}_{side}")
                    for name in EXPECTED_MODES
                } for side in ("l", "r")
            }
        })
        print("READ_ONLY_FOREARM_CONTROL_CAPTURE", len(captures) - 1, flush=True)

    try:
        outcome = bench.run(only=["forearm_rotation"], post_pose=capture)
    finally:
        correction.build_corrected_scene = original_build
    frames = outcome.get("benchmarks", {}).get("forearm_rotation", {}).get("frames", [])
    if len(captures) != 9 or len(frames) != 9:
        raise ValueError("Incomplete authored forearm benchmark")
    pronation_mean = _finite(bench._atlas_mean("forearm_pronation"))
    supination_mean = _finite(bench._atlas_mean("forearm_supination"))
    samples = []
    for sample, (capture_row, frame) in enumerate(zip(captures, frames)):
        angles = frame.get("angles_deg", {})
        samples.append({
            "sample": sample,
            "t": sample / 8.0,
            "authored_target_deg_not_isb": authored_target_deg(
                sample / 8.0, pronation_mean, supination_mean),
            "benchmark_angles_deg_population_means_not_limits": {
                "elbow_flexion": angles.get("elbow_flexion"),
                "forearm_pronation": angles.get("forearm_pronation"),
                "forearm_supination": angles.get("forearm_supination"),
            },
            "evaluated_forearm_skin": {
                "minimum_slice_radius_ratio_l": angles.get(
                    "forearm_min_slice_radius_ratio_l"),
                "minimum_slice_radius_ratio_r": angles.get(
                    "forearm_min_slice_radius_ratio_r"),
                "anatomical_tissue_safety_claimed": False,
            },
            "sides": capture_row["sides"],
        })
    after = adapter.rest_signature(rig, body)
    unchanged = digest(source) == W8_SHA256
    if before != after or not unchanged:
        raise ValueError("Preserved source or in-memory rest bones changed")
    data = {
        "status": "READ_ONLY_AUTHORED_FOREARM_CONTROL_PATH_ANATOMY_NOT_APPROVED",
        "evidence_kind": "NATIVE_PINNED_MODEL_OBSERVATION",
        "synthetic_test_fixture": False,
        "model": "W8",
        "source_sha256": W8_SHA256,
        "pinned_r57_source_commit": R57_SHA,
        "source_unchanged": True,
        "saved_blend": False,
        "rest_bone_signature_unchanged": True,
        "authored_suffixes_not_anatomical_laterality": ["l", "r"],
        "separate_radius_ulna_controls_observed": False,
        "anatomical_joint_coordinate_system_verified": False,
        "pronation_supination_approved": False,
        "return_to_neutral_tested": False,
        "population_means_deg_not_limits": {
            "forearm_pronation": pronation_mean,
            "forearm_supination": supination_mean,
        },
        "samples": samples,
        "limitations": list(REQUIRED_LIMITATIONS),
    }
    errors = validate_report(data)
    if errors:
        raise ValueError("Unusable read-only forearm pose report: " + "; ".join(errors))
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "w8_forearm_pose_state.json").write_text(
        json.dumps(data, indent=2) + "\n", encoding="utf-8")
    (args.out / "w8_forearm_pose_state.md").write_text(markdown(data), encoding="utf-8")
    print("W8_AUTHORED_FOREARM_CONTROL_PATH_WRITTEN", len(samples), flush=True)


if __name__ == "__main__":
    main()
