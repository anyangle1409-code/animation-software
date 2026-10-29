"""READ ONLY: capture the frozen r57 W8 authored squat control trajectory.

The report observes the existing nine-frame FK benchmark in memory. Bone heads
are authored rig control locations, not independently verified joint centres.
No .blend is saved and no anatomy, ground contact or movement is approved.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

W8_SHA256 = "2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c"
R57_SHA = "025d5f28fa7eba2064fba565b1c9b60119cdd2cb"
TARGETS = {
    "pelvis_forward_tilt": 25.0,
    "spine_extension": 10.0,
    "hip_flexion": 110.0,
    "knee_flexion": 110.0,
}
EXPECTED_MODES = {
    "pelvis": "XYZ", "spine_01": "XYZ", "thigh": "XYZ", "shin": "XYZ",
    "foot": "XYZ", "toe": "XYZ",
}


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def finite(value):
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("Nonfinite numerical pose state")
    return result


def smooth(t):
    value = max(0.0, min(1.0, finite(t)))
    return value * value * (3.0 - 2.0 * value)


def q_angle_deg(quaternion):
    """Unsigned matrix-basis rotation magnitude, never an anatomical angle."""
    q = quaternion.copy()
    q.normalize()
    angle = math.degrees(finite(q.angle)) % 360.0
    return min(angle, 360.0 - angle)


def vector3(value):
    result = [finite(component) for component in value]
    if len(result) != 3:
        raise ValueError("3D vector required")
    return result


def bone_record(pose_bones, rig_world, name):
    bone = pose_bones.get(name)
    if bone is None:
        return {"control_present": False}
    return {
        "control_present": True,
        "pose_rotation_mode": bone.rotation_mode,
        "local_delta_angle_deg_not_anatomical": q_angle_deg(
            bone.matrix_basis.to_quaternion()),
        "head_world_m_not_anatomical_joint_centre": vector3(rig_world @ bone.head),
        "tail_world_m": vector3(rig_world @ bone.tail),
    }


def _subtract(a, b):
    return [finite(x) - finite(y) for x, y in zip(vector3(a), vector3(b))]


def plant_stage_record(rig, rest_heads):
    bones = rig.pose.bones
    sides = {}
    for side in ("l", "r"):
        foot = bones[f"foot_{side}"]
        sides[side] = {
            "foot_head_world_m": vector3(rig.matrix_world @ foot.head),
            "rest_target_head_world_m": vector3(rig.matrix_world @ rest_heads[side]),
            "foot_local_delta_deg": q_angle_deg(foot.matrix_basis.to_quaternion()),
        }
    return {
        "root_matrix_basis_translation_m": vector3(
            bones["root"].matrix_basis.to_translation()),
        "sides": sides,
    }


def plant_solve_summary(pre, post):
    result = {
        "pre_root_matrix_basis_translation_m": vector3(
            pre["root_matrix_basis_translation_m"]),
        "post_root_matrix_basis_translation_m": vector3(
            post["root_matrix_basis_translation_m"]),
        "root_matrix_basis_translation_delta_m": _subtract(
            post["root_matrix_basis_translation_m"],
            pre["root_matrix_basis_translation_m"]),
        "sides": {},
    }
    for side in ("l", "r"):
        before, after = pre["sides"][side], post["sides"][side]
        target = vector3(before["rest_target_head_world_m"])
        if target != vector3(after["rest_target_head_world_m"]):
            raise ValueError("foot-plant rest target changed during solve")
        result["sides"][side] = {
            "rest_target_head_world_m_not_verified_joint_centre": target,
            "pre_solve_foot_head_world_m": vector3(before["foot_head_world_m"]),
            "pre_solve_residual_world_m": _subtract(before["foot_head_world_m"], target),
            "post_solve_foot_head_world_m": vector3(after["foot_head_world_m"]),
            "post_solve_residual_world_m": _subtract(after["foot_head_world_m"], target),
            "pre_solve_foot_local_delta_deg_not_anatomical": finite(
                before["foot_local_delta_deg"]),
            "post_solve_foot_local_delta_deg_not_anatomical": finite(
                after["foot_local_delta_deg"]),
        }
    result["mean_post_solve_residual_world_m"] = [
        sum(result["sides"][side]["post_solve_residual_world_m"][axis]
            for side in ("l", "r")) / 2.0 for axis in range(3)
    ]
    return result


def _valid_vector(value):
    return (isinstance(value, list) and len(value) == 3
            and all(type(x) in (int, float) and math.isfinite(x) for x in value))


def _vectors_close(a, b, tolerance=1e-9):
    return (_valid_vector(a) and _valid_vector(b)
            and all(math.isclose(x, y, abs_tol=tolerance) for x, y in zip(a, b)))


def _valid_plant_solve(solve, final_root):
    if not isinstance(solve, dict) or not _vectors_close(
            solve.get("post_root_matrix_basis_translation_m"), final_root):
        return False
    pre_root = solve.get("pre_root_matrix_basis_translation_m")
    post_root = solve.get("post_root_matrix_basis_translation_m")
    if (not _valid_vector(pre_root) or not _valid_vector(post_root)
            or not _vectors_close(solve.get("root_matrix_basis_translation_delta_m"),
                                  [b - a for a, b in zip(pre_root, post_root)])):
        return False
    sides = solve.get("sides")
    if not isinstance(sides, dict) or set(sides) != {"l", "r"}:
        return False
    post_residuals = []
    for side in ("l", "r"):
        row = sides[side]
        if not isinstance(row, dict):
            return False
        target = row.get("rest_target_head_world_m_not_verified_joint_centre")
        pre = row.get("pre_solve_foot_head_world_m")
        post = row.get("post_solve_foot_head_world_m")
        if (not _valid_vector(target) or not _valid_vector(pre) or not _valid_vector(post)
                or not _vectors_close(row.get("pre_solve_residual_world_m"),
                                      [a - b for a, b in zip(pre, target)])
                or not _vectors_close(row.get("post_solve_residual_world_m"),
                                      [a - b for a, b in zip(post, target)])):
            return False
        for key in ("pre_solve_foot_local_delta_deg_not_anatomical",
                    "post_solve_foot_local_delta_deg_not_anatomical"):
            angle = row.get(key)
            if (type(angle) not in (int, float) or not math.isfinite(angle)
                    or not 0.0 <= angle <= 180.000001):
                return False
        post_residuals.append(row["post_solve_residual_world_m"])
    mean = [sum(row[axis] for row in post_residuals) / 2.0 for axis in range(3)]
    return _vectors_close(solve.get("mean_post_solve_residual_world_m"), mean)


def validate_report(data):
    errors = []
    if (data.get("status") != "READ_ONLY_AUTHORED_SQUAT_CONTROL_STATE_ANATOMY_NOT_APPROVED"
            or data.get("model") != "W8" or data.get("source_sha256") != W8_SHA256
            or data.get("pinned_r57_source_commit") != R57_SHA
            or data.get("source_unchanged") is not True
            or data.get("rest_bone_signature_unchanged") is not True
            or data.get("saved_blend") is not False
            or data.get("anatomical_approval") != "NOT_GRANTED"
            or data.get("ground_contact_approval") != "NOT_GRANTED"):
        errors.append("invalid evidence scope")
    samples = data.get("samples")
    if (not isinstance(samples, list) or len(samples) != 9
            or [row.get("sample") for row in samples] != list(range(9))):
        errors.append("samples 0 through 8 required")
        return errors
    for index, row in enumerate(samples):
        expected_t = index / 8.0
        if type(row.get("t")) not in (int, float) or not math.isclose(
                row["t"], expected_t, abs_tol=1e-12):
            errors.append("invalid sample parameter")
        expected = {name: peak * smooth(expected_t) for name, peak in TARGETS.items()}
        targets = row.get("authored_targets_deg_not_measured")
        if (not isinstance(targets, dict) or set(targets) != set(expected)
                or any(type(targets.get(name)) not in (int, float)
                       or not math.isfinite(targets[name])
                       or not math.isclose(targets[name], value, abs_tol=1e-6)
                       for name, value in expected.items())):
            errors.append("authored target drift")
        ankle = row.get("measured_authored_ankle_dorsiflexion_deg_not_isb")
        lowest = row.get("evaluated_body_lowest_world_z_m_not_contact")
        if type(ankle) not in (int, float) or not math.isfinite(ankle):
            errors.append("invalid authored ankle measurement")
        if type(lowest) not in (int, float) or not math.isfinite(lowest):
            errors.append("invalid evaluated body floor proxy")
        if not _valid_vector(row.get("root_matrix_basis_translation_m")):
            errors.append("invalid root translation")
        elif not _valid_plant_solve(
                row.get("foot_plant_solve"), row["root_matrix_basis_translation_m"]):
            errors.append("invalid foot-plant solve evidence")
        controls = []
        centreline = row.get("centreline")
        if not isinstance(centreline, dict) or set(centreline) != {"pelvis", "spine_01"}:
            errors.append("missing authored centreline controls")
        else:
            controls.extend((name, centreline[name]) for name in ("pelvis", "spine_01"))
        sides = row.get("sides")
        if not isinstance(sides, dict) or set(sides) != {"l", "r"}:
            errors.append("both runtime suffix sides required")
            continue
        for side in ("l", "r"):
            if not isinstance(sides[side], dict) or set(sides[side]) != {"thigh", "shin", "foot", "toe"}:
                errors.append("missing authored lower-limb controls")
                continue
            controls.extend((name, sides[side][name]) for name in ("thigh", "shin", "foot", "toe"))
        for name, control in controls:
            if not isinstance(control, dict) or control.get("control_present") is not True:
                errors.append("missing authored lower-limb control")
                continue
            if control.get("pose_rotation_mode") != EXPECTED_MODES[name]:
                errors.append("unexpected authored control rotation mode")
            angle = control.get("local_delta_angle_deg_not_anatomical")
            if (type(angle) not in (int, float) or not math.isfinite(angle)
                    or not 0.0 <= angle <= 180.000001):
                errors.append("invalid local delta")
            if (not _valid_vector(control.get("head_world_m_not_anatomical_joint_centre"))
                    or not _valid_vector(control.get("tail_world_m"))):
                errors.append("invalid authored control trajectory point")
    return errors


def markdown(data):
    errors = validate_report(data)
    if errors:
        raise ValueError("invalid squat pose report: " + "; ".join(errors))
    lines = [
        "# W8 9-frame authored squat-control observations", "",
        "These are actual frozen-r57 authored-control states. Local deltas are unsigned matrix-basis magnitudes; control heads are authored rig locations.",
        "They are **not ISB hip/knee/ankle angles**, independently verified joint centres, balance evidence, or movement approval.", "",
        "| Sample | Hip target° | Knee target° | Pelvis target° | Spine target° | measured authored ankle DF° | root Z m | lowest evaluated body Z m |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in data["samples"]:
        target = row["authored_targets_deg_not_measured"]
        lines.append(
            f"| {row['sample']} | {target['hip_flexion']:.5f} | {target['knee_flexion']:.5f} | "
            f"{target['pelvis_forward_tilt']:.5f} | {target['spine_extension']:.5f} | "
            f"{row['measured_authored_ankle_dorsiflexion_deg_not_isb']:.5f} | "
            f"{row['root_matrix_basis_translation_m'][2]:.7f} | "
            f"{row['evaluated_body_lowest_world_z_m_not_contact']:.7f} |")
    lines += ["", "## Foot-plant solve residuals", "",
              "Residuals are foot-control head minus its captured rest target after the frozen solve; they are not anatomical ankle-centre errors.", "",
              "| Sample | root correction X/Y/Z mm | l post residual X/Y/Z mm | r post residual X/Y/Z mm | mean post residual X/Y/Z mm |",
              "|---:|---:|---:|---:|---:|"]
    for row in data["samples"]:
        solve = row["foot_plant_solve"]
        def millimetres(values):
            return "/".join(f"{value * 1000:.5f}" for value in values)
        lines.append(
            f"| {row['sample']} | {millimetres(solve['root_matrix_basis_translation_delta_m'])} | "
            f"{millimetres(solve['sides']['l']['post_solve_residual_world_m'])} | "
            f"{millimetres(solve['sides']['r']['post_solve_residual_world_m'])} | "
            f"{millimetres(solve['mean_post_solve_residual_world_m'])} |")
    lines += ["", "The benchmark solves foot orientation and applies one averaged root correction, but this is **NOT verified ground contact** or pressure/balance evidence.",
              "Toe controls remain observed even when their local delta is zero; no multisegment foot anatomy is inferred.", ""]
    return "\n".join(lines)


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
    original_metric = bench.frame_metrics
    original_plant_feet = bench._plant_feet
    captures = []
    plant_records = []
    correction.build_corrected_scene = lambda: result

    def tracked_plant_feet(loaded_rig, rest_heads):
        pre = plant_stage_record(loaded_rig, rest_heads)
        original_plant_feet(loaded_rig, rest_heads)
        post = plant_stage_record(loaded_rig, rest_heads)
        plant_records.append(plant_solve_summary(pre, post))

    bench._plant_feet = tracked_plant_feet

    def capture(V0, V, F, dom, rest_floor):
        sample = len(captures)
        t = sample / 8.0
        k = smooth(t)
        bones = rig.pose.bones
        if len(plant_records) != sample + 1:
            raise ValueError("Expected exactly one foot-plant solve per squat sample")
        row = {
            "sample": sample,
            "t": t,
            "authored_targets_deg_not_measured": {
                name: peak * k for name, peak in TARGETS.items()
            },
            "measured_authored_ankle_dorsiflexion_deg_not_isb": max(
                finite(bench._ankle_dorsiflexion_deg(rig, side)) for side in ("l", "r")),
            "root_matrix_basis_translation_m": vector3(
                bones["root"].matrix_basis.to_translation()),
            "evaluated_body_lowest_world_z_m_not_contact": min(finite(vertex.z) for vertex in V),
            "foot_plant_solve": plant_records[sample],
            "centreline": {
                name: bone_record(bones, rig.matrix_world, name)
                for name in ("pelvis", "spine_01")
            },
            "sides": {
                side: {
                    name: bone_record(bones, rig.matrix_world, f"{name}_{side}")
                    for name in ("thigh", "shin", "foot", "toe")
                } for side in ("l", "r")
            },
        }
        captures.append(row)
        print("READ_ONLY_SQUAT_CONTROL_CAPTURE", sample, flush=True)
        return original_metric(V0, V, F, dom, rest_floor)

    bench.frame_metrics = capture
    try:
        outcome = bench.run(
            only=["squat"], post_pose=lambda loaded: drives.drive(
                loaded["runtime"], loaded["body"]))
    finally:
        bench.frame_metrics = original_metric
        bench._plant_feet = original_plant_feet
        correction.build_corrected_scene = original_build
    after = adapter.rest_signature(rig, body)
    unchanged = digest(source) == W8_SHA256
    if before != after or not unchanged:
        raise ValueError("Preserved source or in-memory rest bones changed")
    if (len(captures) != 9 or len(plant_records) != 9
            or len(outcome["benchmarks"]["squat"]["frames"]) != 9):
        raise ValueError("Incomplete authored squat benchmark")
    data = {
        "status": "READ_ONLY_AUTHORED_SQUAT_CONTROL_STATE_ANATOMY_NOT_APPROVED",
        "model": "W8", "source_sha256": W8_SHA256,
        "pinned_r57_source_commit": R57_SHA,
        "source_unchanged": True, "saved_blend": False,
        "rest_bone_signature_unchanged": True,
        "anatomical_approval": "NOT_GRANTED", "ground_contact_approval": "NOT_GRANTED",
        "samples": captures,
        "limitations": [
            "Authored FK controls and world-space control trajectories are not ISB joint-coordinate measurements",
            "Bone heads are authored rig locations, not independently verified anatomical joint centres",
            "The benchmark foot solve and lowest evaluated vertex do not prove pressure, balance or ground contact",
            "Pre/post solve residuals expose authored root-correction behavior, not anatomical foot planting",
            "The single foot and toe controls do not establish talus, calcaneus or multisegment foot coordination",
            "Population range-of-motion means are not hard movement limits and no movement is approved",
        ],
    }
    errors = validate_report(data)
    if errors:
        raise ValueError("Unusable read-only squat pose report: " + "; ".join(errors))
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "w8_authored_squat_control_state.json").write_text(
        json.dumps(data, indent=2) + "\n", encoding="utf-8")
    (args.out / "w8_authored_squat_control_state.md").write_text(
        markdown(data), encoding="utf-8")
    print("W8_AUTHORED_SQUAT_CONTROL_STATE_WRITTEN", len(captures), flush=True)


if __name__ == "__main__":
    main()
