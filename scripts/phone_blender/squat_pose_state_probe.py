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
CORRECTIVE_RETURN_LIMITATION = (
    "Skeletal matrix-basis reset and corrective driver refresh are lifecycle "
    "observations, not proof of anatomical neutral or tissue safety")


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


def geometry_delta_summary(reference_vertices, observed_vertices):
    """Summarize same-topology evaluated geometry without retaining it in JSON."""
    if (not isinstance(reference_vertices, (list, tuple))
            or not isinstance(observed_vertices, (list, tuple))
            or not reference_vertices
            or len(reference_vertices) != len(observed_vertices)):
        raise ValueError("same nonempty vertex topology required")
    distances_mm = []
    for reference, observed in zip(reference_vertices, observed_vertices):
        for point in (reference, observed):
            if (not isinstance(point, (list, tuple)) or len(point) != 3
                    or any(type(value) not in (int, float) for value in point)):
                raise ValueError("strict numerical 3D vector required")
        a, b = vector3(reference), vector3(observed)
        distances_mm.append(math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b))) * 1000.0)
    return {
        "vertex_count": len(distances_mm),
        "change_threshold_mm": 0.000001,
        "changed_vertex_count_over_1e-6_mm": sum(
            distance > 0.000001 for distance in distances_mm),
        "max_displacement_mm": max(distances_mm),
        "rms_displacement_mm": math.sqrt(sum(
            distance * distance for distance in distances_mm) / len(distances_mm)),
    }


def shape_key_state(key_blocks):
    """Fingerprint all shape-key values and list active keys deterministically."""
    rows = []
    for key in key_blocks:
        name, value = getattr(key, "name", None), getattr(key, "value", None)
        if not isinstance(name, str) or not name:
            raise ValueError("nonempty shape-key name required")
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError("finite numerical shape-key value required")
        rows.append((name, float(value)))
    rows.sort()
    if len({name for name, _ in rows}) != len(rows):
        raise ValueError("duplicate shape-key name")
    encoded = json.dumps(rows, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    active = [
        {"name": name, "value": value} for name, value in rows if value != 0.0]
    return {
        "key_count": len(rows),
        "all_values_sha256": hashlib.sha256(encoded).hexdigest(),
        "nonzero_values_sha256": hashlib.sha256(json.dumps(
            active, separators=(",", ":"), sort_keys=True).encode("utf-8")).hexdigest(),
        "nonzero_keys": active,
    }


def skeletal_basis_state(pose_bones):
    rows = []
    for bone in pose_bones:
        name = getattr(bone, "name", None)
        if not isinstance(name, str) or not name:
            raise ValueError("named pose bones required")
        rotation = q_angle_deg(bone.matrix_basis.to_quaternion())
        translation = vector3(bone.matrix_basis.to_translation())
        translation_mm = math.sqrt(sum(value * value for value in translation)) * 1000.0
        rows.append((name, rotation, translation_mm))
    rows.sort()
    if not rows or len({name for name, _, _ in rows}) != len(rows):
        raise ValueError("pose bones required")
    max_rotation = max(row[1] for row in rows)
    max_translation = max(row[2] for row in rows)
    max_rotation_control = min(row[0] for row in rows if row[1] == max_rotation)
    max_translation_control = min(row[0] for row in rows if row[2] == max_translation)
    residuals = [
        {"name": name,
         "rotation_deg_not_anatomical": rotation,
         "translation_mm": translation}
        for name, rotation, translation in rows
        if rotation > 0.000001 or translation > 0.000001
    ]
    return {
        "pose_bone_count": len(rows),
        "control_names_sha256": hashlib.sha256(json.dumps(
            [row[0] for row in rows], separators=(",", ":")).encode("utf-8")).hexdigest(),
        "control_state_sha256": hashlib.sha256(json.dumps(
            rows, separators=(",", ":")).encode("utf-8")).hexdigest(),
        "residual_controls_sha256": hashlib.sha256(json.dumps(
            residuals, separators=(",", ":")).encode("utf-8")).hexdigest(),
        "max_matrix_basis_rotation_deg_not_anatomical": max_rotation,
        "max_rotation_control": max_rotation_control,
        "max_matrix_basis_translation_mm": max_translation,
        "max_translation_control": max_translation_control,
        "controls_over_identity_tolerance": residuals,
        "all_matrix_basis_identity_within_tolerance": (
            max_rotation <= 0.000001 and max_translation <= 0.000001),
    }


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


def run_tracked_plant_solve(rig, rest_heads, update, original_solve,
                            stage=plant_stage_record):
    """Observe the evaluated state on both sides of the unchanged solve."""
    update()
    pre = stage(rig, rest_heads)
    original_solve(rig, rest_heads)
    update()
    post = stage(rig, rest_heads)
    return pre, post


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


def foot_skin_lower_envelope(vertices, dominant_groups, side, foot_control_head,
                             lower_fraction=0.01):
    """Describe evaluated foot/toe-dominant skin; never infer physical contact."""
    if len(vertices) != len(dominant_groups) or not vertices:
        raise ValueError("vertex/group count mismatch or empty geometry")
    if side not in ("l", "r") or lower_fraction != 0.01:
        raise ValueError("unsupported authored suffix or lower fraction")
    selected = []
    names = set()
    for vertex_id, (vertex, group) in enumerate(zip(vertices, dominant_groups)):
        if (isinstance(group, str) and group.endswith("_" + side)
                and group.split("_")[0] in ("foot", "toe")):
            selected.append((vertex_id, vector3(vertex)))
            names.add(group)
    if not selected:
        raise ValueError("no foot/toe-dominant skin vertices for authored suffix")
    count = max(1, math.ceil(len(selected) * lower_fraction))
    lower = sorted(selected, key=lambda row: (row[1][2], row[0]))[:count]
    ids = [row[0] for row in lower]
    points = [row[1] for row in lower]
    centroid = [sum(point[axis] for point in points) / count for axis in range(3)]
    bounds = {
        "min": [min(point[axis] for point in points) for axis in range(3)],
        "max": [max(point[axis] for point in points) for axis in range(3)],
    }
    selected_ids = [row[0] for row in selected]
    return {
        "evaluated_mesh_vertex_count": len(vertices),
        "selected_vertex_count": len(selected),
        "selected_vertex_ids_sha256": hashlib.sha256(json.dumps(
            selected_ids, separators=(",", ":")).encode("utf-8")).hexdigest(),
        "dominant_group_names": sorted(names),
        "lower_fraction": lower_fraction,
        "lower_vertex_count": count,
        "lower_vertex_ids": ids,
        "minimum_world_z_m": min(point[2] for _, point in selected),
        "lower_centroid_world_m": centroid,
        "lower_bounds_world_m": bounds,
        "foot_control_head_minus_lower_centroid_world_m": _subtract(
            foot_control_head, centroid),
    }


def skin_control_relative_motion(samples):
    """Cross-reference authored foot controls and skin without contact claims."""
    if not isinstance(samples, list) or not samples:
        raise ValueError("ordered pose samples required")
    reference = {}
    rows = []
    for sample_index, sample in enumerate(samples):
        sides = {}
        for side in ("l", "r"):
            head = vector3(sample["sides"][side]["foot"][
                "head_world_m_not_anatomical_joint_centre"])
            centroid = vector3(sample["foot_skin_lower_envelope"]["sides"][side][
                "lower_centroid_world_m"])
            relative = _subtract(head, centroid)
            if sample_index == 0:
                reference[side] = relative
            sides[side] = {
                "foot_control_head_minus_lower_centroid_world_m": relative,
                "change_from_sample0_world_m": _subtract(relative, reference[side]),
            }
        rows.append({"sample": sample["sample"], "sides": sides})
    return {
        "status": "DESCRIPTIVE_FOOT_CONTROL_TO_SKIN_LOWER_CENTROID_RELATIVE_MOTION_NOT_CONTACT",
        "contact_claimed": False,
        "reference_sample": 0,
        "samples": rows,
    }


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


def _valid_skin_envelope(envelope):
    if (not isinstance(envelope, dict)
            or envelope.get("status") != "DESCRIPTIVE_EVALUATED_FOOT_SKIN_LOWER_ENVELOPE_NOT_CONTACT"
            or envelope.get("contact_claimed") is not False):
        return False
    sides = envelope.get("sides")
    if not isinstance(sides, dict) or set(sides) != {"l", "r"}:
        return False
    for side in ("l", "r"):
        row = sides[side]
        mesh_count = row.get("evaluated_mesh_vertex_count")
        selected = row.get("selected_vertex_count")
        lower_count = row.get("lower_vertex_count")
        ids = row.get("lower_vertex_ids")
        digest_value = row.get("selected_vertex_ids_sha256")
        groups = row.get("dominant_group_names")
        if (type(mesh_count) is not int or mesh_count <= 0
                or type(selected) is not int or not 0 < selected <= mesh_count
                or row.get("lower_fraction") != 0.01
                or type(lower_count) is not int
                or lower_count != max(1, math.ceil(selected * 0.01))
                or not isinstance(ids, list) or len(ids) != lower_count
                or any(type(vertex_id) is not int or not 0 <= vertex_id < mesh_count
                       for vertex_id in ids)
                or len(set(ids)) != len(ids)
                or not isinstance(digest_value, str) or len(digest_value) != 64
                or any(char not in "0123456789abcdef" for char in digest_value)
                or not isinstance(groups, list) or groups != sorted(set(groups)) or not groups
                or any(not name.endswith("_" + side)
                       or name.split("_")[0] not in ("foot", "toe") for name in groups)):
            return False
        centroid = row.get("lower_centroid_world_m")
        bounds = row.get("lower_bounds_world_m")
        minimum = row.get("minimum_world_z_m")
        if (not _valid_vector(centroid) or not isinstance(bounds, dict)
                or set(bounds) != {"min", "max"}
                or not _valid_vector(bounds["min"]) or not _valid_vector(bounds["max"])
                or type(minimum) not in (int, float) or not math.isfinite(minimum)
                or not math.isclose(minimum, bounds["min"][2], abs_tol=1e-9)
                or any(not bounds["min"][axis] <= centroid[axis] <= bounds["max"][axis]
                       for axis in range(3))
                or not _valid_vector(row.get(
                    "foot_control_head_minus_lower_centroid_world_m"))):
            return False
    return True


def _valid_skin_control_relative_motion(record):
    if (not isinstance(record, dict)
            or record.get("status") !=
            "DESCRIPTIVE_FOOT_CONTROL_TO_SKIN_LOWER_CENTROID_RELATIVE_MOTION_NOT_CONTACT"
            or record.get("contact_claimed") is not False
            or type(record.get("reference_sample")) is not int
            or record["reference_sample"] != 0):
        return False
    samples = record.get("samples")
    if (not isinstance(samples, list) or len(samples) != 9
            or [row.get("sample") for row in samples] != list(range(9))):
        return False
    for row in samples:
        sides = row.get("sides")
        if not isinstance(sides, dict) or set(sides) != {"l", "r"}:
            return False
        for side in ("l", "r"):
            relative = sides[side]
            if (not isinstance(relative, dict)
                    or not _valid_vector(relative.get(
                        "foot_control_head_minus_lower_centroid_world_m"))
                    or not _valid_vector(relative.get(
                        "change_from_sample0_world_m"))):
                return False
    return True


def _valid_shape_key_state(state):
    if not isinstance(state, dict) or set(state) != {
            "key_count", "all_values_sha256", "nonzero_values_sha256",
            "nonzero_keys"}:
        return False
    count, fingerprint, active = (
        state["key_count"], state["all_values_sha256"], state["nonzero_keys"])
    if (type(count) is not int or count <= 0
            or not isinstance(fingerprint, str) or len(fingerprint) != 64
            or any(char not in "0123456789abcdef" for char in fingerprint)
            or not isinstance(active, list) or len(active) > count):
        return False
    names = []
    for row in active:
        if (not isinstance(row, dict) or set(row) != {"name", "value"}
                or not isinstance(row["name"], str) or not row["name"]
                or type(row["value"]) not in (int, float)
                or not math.isfinite(row["value"]) or row["value"] == 0.0):
            return False
        names.append(row["name"])
    if names != sorted(set(names)):
        return False
    expected = hashlib.sha256(json.dumps(
        active, separators=(",", ":"), sort_keys=True).encode("utf-8")).hexdigest()
    return state["nonzero_values_sha256"] == expected


def _valid_geometry_delta(summary):
    if not isinstance(summary, dict) or set(summary) != {
            "vertex_count", "change_threshold_mm",
            "changed_vertex_count_over_1e-6_mm", "max_displacement_mm",
            "rms_displacement_mm"}:
        return False
    count, changed = summary["vertex_count"], summary[
        "changed_vertex_count_over_1e-6_mm"]
    if (type(count) is not int or count <= 0 or type(changed) is not int
            or not 0 <= changed <= count
            or type(summary["change_threshold_mm"]) not in (int, float)
            or summary["change_threshold_mm"] != 0.000001):
        return False
    maximum, rms = summary["max_displacement_mm"], summary["rms_displacement_mm"]
    threshold = summary["change_threshold_mm"]
    return (type(maximum) in (int, float) and math.isfinite(maximum)
            and type(rms) in (int, float) and math.isfinite(rms)
            and 0.0 <= rms <= maximum + 1e-12
            and ((changed == 0 and maximum <= threshold)
                 or (changed > 0 and maximum > threshold and rms >
                     threshold * math.sqrt(changed / count))))


def _valid_skeletal_basis(state):
    if not isinstance(state, dict) or set(state) != {
            "pose_bone_count", "control_names_sha256", "control_state_sha256",
            "residual_controls_sha256",
            "max_matrix_basis_rotation_deg_not_anatomical", "max_rotation_control",
            "max_matrix_basis_translation_mm", "max_translation_control",
            "controls_over_identity_tolerance",
            "all_matrix_basis_identity_within_tolerance"}:
        return False
    rotation = state["max_matrix_basis_rotation_deg_not_anatomical"]
    translation = state["max_matrix_basis_translation_mm"]
    digest_values = (state["control_names_sha256"], state["control_state_sha256"],
                     state["residual_controls_sha256"])
    residuals = state["controls_over_identity_tolerance"]
    expected = rotation <= 0.000001 and translation <= 0.000001
    if not (type(state["pose_bone_count"]) is int and state["pose_bone_count"] == 77
            and all(isinstance(value, str) and len(value) == 64
                    and all(char in "0123456789abcdef" for char in value)
                    for value in digest_values)
            and type(rotation) in (int, float) and math.isfinite(rotation)
            and type(translation) in (int, float) and math.isfinite(translation)
            and rotation >= 0.0 and translation >= 0.0
            and isinstance(state["max_rotation_control"], str)
            and bool(state["max_rotation_control"])
            and isinstance(state["max_translation_control"], str)
            and bool(state["max_translation_control"])
            and isinstance(residuals, list)
            and len(residuals) <= state["pose_bone_count"]
            and state["all_matrix_basis_identity_within_tolerance"] is expected):
        return False
    names = []
    for row in residuals:
        if (not isinstance(row, dict) or set(row) != {
                "name", "rotation_deg_not_anatomical", "translation_mm"}
                or not isinstance(row["name"], str) or not row["name"]
                or type(row["rotation_deg_not_anatomical"]) not in (int, float)
                or not math.isfinite(row["rotation_deg_not_anatomical"])
                or type(row["translation_mm"]) not in (int, float)
                or not math.isfinite(row["translation_mm"])
                or row["rotation_deg_not_anatomical"] < 0.0
                or row["translation_mm"] < 0.0
                or (row["rotation_deg_not_anatomical"] <= 0.000001
                    and row["translation_mm"] <= 0.000001)
                or row["rotation_deg_not_anatomical"] > rotation
                or row["translation_mm"] > translation):
            return False
        names.append(row["name"])
    if names != sorted(set(names)) or bool(residuals) is expected:
        return False
    expected_residual_digest = hashlib.sha256(json.dumps(
        residuals, separators=(",", ":")).encode("utf-8")).hexdigest()
    if state["residual_controls_sha256"] != expected_residual_digest:
        return False
    if rotation > 0.000001 and not any(
            row["name"] == state["max_rotation_control"]
            and row["rotation_deg_not_anatomical"] == rotation for row in residuals):
        return False
    if translation > 0.000001 and not any(
            row["name"] == state["max_translation_control"]
            and row["translation_mm"] == translation for row in residuals):
        return False
    return True


def _valid_corrective_return(record, expected_vertex_count):
    if (not isinstance(record, dict)
            or record.get("status") !=
            "DESCRIPTIVE_SKELETAL_RESET_CORRECTIVE_LIFECYCLE_NOT_ANATOMY"
            or record.get("anatomical_approval") != "NOT_GRANTED"
            or record.get("tissue_safety_claimed") is not False):
        return False
    reference = record.get("sample0_reference")
    if (not isinstance(reference, dict) or set(reference) != {"sample", "shape_keys"}
            or type(reference["sample"]) is not int or reference["sample"] != 0
            or not _valid_shape_key_state(reference["shape_keys"])):
        return False
    stages = record.get("stages")
    expected = [
        ("AFTER_BENCHMARK_SKELETAL_RESET_BEFORE_NEUTRAL_DRIVER_REFRESH", False, 0),
        ("AFTER_NEUTRAL_DRIVER_REFRESH", True, 1),
        ("AFTER_SECOND_NEUTRAL_DRIVER_REFRESH", True, 2),
    ]
    if not isinstance(stages, list) or len(stages) != 3:
        return False
    vertex_count = None
    expected_key_count = reference["shape_keys"]["key_count"]
    control_names_sha256 = None
    for stage, (label, refreshed, refresh_count) in zip(stages, expected):
        if (not isinstance(stage, dict) or set(stage) != {
                "stage", "neutral_driver_refresh_applied",
                "neutral_driver_refresh_count", "skeletal_basis",
                "shape_keys", "evaluated_geometry_vs_sample0"}
                or stage["stage"] != label
                or stage["neutral_driver_refresh_applied"] is not refreshed
                or type(stage["neutral_driver_refresh_count"]) is not int
                or stage["neutral_driver_refresh_count"] != refresh_count
                or not _valid_skeletal_basis(stage["skeletal_basis"])
                or not _valid_shape_key_state(stage["shape_keys"])
                or stage["shape_keys"]["key_count"] != expected_key_count
                or not _valid_geometry_delta(stage["evaluated_geometry_vs_sample0"])):
            return False
        current = stage["evaluated_geometry_vs_sample0"]["vertex_count"]
        if vertex_count is not None and current != vertex_count:
            return False
        vertex_count = current
        current_names = stage["skeletal_basis"]["control_names_sha256"]
        if control_names_sha256 is not None and current_names != control_names_sha256:
            return False
        control_names_sha256 = current_names
    repeat = record.get("repeat_refresh_comparison")
    if (not isinstance(repeat, dict) or set(repeat) != {
            "status", "first_refresh_count", "second_refresh_count",
            "skeletal_control_state_sha256_equal",
            "shape_key_all_values_sha256_equal",
            "evaluated_geometry_first_to_second"}
            or repeat["status"] !=
            "DESCRIPTIVE_REPEAT_NEUTRAL_DRIVER_IDEMPOTENCE_NOT_ANATOMY"
            or type(repeat["first_refresh_count"]) is not int
            or repeat["first_refresh_count"] != 1
            or type(repeat["second_refresh_count"]) is not int
            or repeat["second_refresh_count"] != 2
            or repeat["skeletal_control_state_sha256_equal"] is not (
                stages[1]["skeletal_basis"]["control_state_sha256"] ==
                stages[2]["skeletal_basis"]["control_state_sha256"])
            or repeat["shape_key_all_values_sha256_equal"] is not (
                stages[1]["shape_keys"]["all_values_sha256"] ==
                stages[2]["shape_keys"]["all_values_sha256"])
            or not _valid_geometry_delta(repeat["evaluated_geometry_first_to_second"])
            or repeat["evaluated_geometry_first_to_second"]["vertex_count"] !=
            expected_vertex_count):
        return False
    return vertex_count == expected_vertex_count


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
    try:
        expected_relative_motion = skin_control_relative_motion(samples)
    except (KeyError, TypeError, ValueError):
        expected_relative_motion = None
    relative_motion = data.get("skin_control_relative_motion")
    if (expected_relative_motion is None
            or not _valid_skin_control_relative_motion(relative_motion)
            or relative_motion != expected_relative_motion):
        errors.append("invalid skin/control relative motion")
    mesh_counts = set()
    try:
        for sample in samples:
            for side in ("l", "r"):
                mesh_counts.add(sample["foot_skin_lower_envelope"]["sides"][side][
                    "evaluated_mesh_vertex_count"])
    except (KeyError, TypeError):
        pass
    expected_vertex_count = next(iter(mesh_counts)) if len(mesh_counts) == 1 else None
    if not _valid_corrective_return(
            data.get("corrective_return_to_neutral"), expected_vertex_count):
        errors.append("invalid corrective return-to-neutral evidence")
    limitations = data.get("limitations")
    if (not isinstance(limitations, list)
            or CORRECTIVE_RETURN_LIMITATION not in limitations):
        errors.append("missing corrective return-to-neutral limitation")
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
        if not _valid_skin_envelope(row.get("foot_skin_lower_envelope")):
            errors.append("invalid foot-skin lower envelope")
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
        envelope = row.get("foot_skin_lower_envelope")
        if _valid_skin_envelope(envelope):
            for side in ("l", "r"):
                skin = envelope["sides"][side]
                foot_head = sides[side]["foot"].get(
                    "head_world_m_not_anatomical_joint_centre")
                if (not _valid_vector(foot_head) or not _vectors_close(
                        skin["foot_control_head_minus_lower_centroid_world_m"],
                        [a - b for a, b in zip(
                            foot_head, skin["lower_centroid_world_m"])])):
                    errors.append("foot-skin/control cross-reference mismatch")
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
    for side in ("l", "r"):
        signatures = []
        for row in samples:
            envelope = row.get("foot_skin_lower_envelope")
            if not _valid_skin_envelope(envelope):
                continue
            skin = envelope["sides"][side]
            signatures.append((skin["selected_vertex_count"],
                               skin["selected_vertex_ids_sha256"],
                               tuple(skin["dominant_group_names"])))
        if signatures and len(set(signatures)) != 1:
            errors.append("foot-skin selection changed across samples")
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
    lines += ["", "## Evaluated foot-skin lower envelope (not contact)", "",
              "The lowest 1% is selected independently per authored suffix from evaluated vertices whose dominant group token is foot or toe.", "",
              "| Sample | Suffix | selected | lower vertices | centroid X/Y/Z mm | lower X span mm | lower Y span mm |",
              "|---:|:---:|---:|---:|---:|---:|---:|"]
    for row in data["samples"]:
        for side in ("l", "r"):
            skin = row["foot_skin_lower_envelope"]["sides"][side]
            bounds = skin["lower_bounds_world_m"]
            centroid = "/".join(
                f"{value * 1000:.3f}" for value in skin["lower_centroid_world_m"])
            lines.append(
                f"| {row['sample']} | {side} | {skin['selected_vertex_count']} | "
                f"{skin['lower_vertex_count']} | {centroid} | "
                f"{(bounds['max'][0] - bounds['min'][0]) * 1000:.3f} | "
                f"{(bounds['max'][1] - bounds['min'][1]) * 1000:.3f} |")
    lines += ["", "These vertices are a descriptive lower envelope only; no floor plane, support polygon, force, pressure, friction, slip or balance threshold is inferred.",
              "", "## Authored foot control relative to skin lower centroid (not contact)", "",
              "Vectors are authored foot-control head minus evaluated skin lower centroid in world space; changes use sample 0 as the descriptive reference.", "",
              "| Sample | Suffix | head minus centroid X/Y/Z mm | change from sample 0 X/Y/Z mm |",
              "|---:|:---:|---:|---:|"]
    for row in data["skin_control_relative_motion"]["samples"]:
        for side in ("l", "r"):
            relative = row["sides"][side]
            vector = "/".join(f"{value * 1000:.3f}" for value in relative[
                "foot_control_head_minus_lower_centroid_world_m"])
            change = "/".join(f"{value * 1000:.3f}" for value in relative[
                "change_from_sample0_world_m"])
            lines.append(f"| {row['sample']} | {side} | {vector} | {change} |")
    lines += ["", "This is a geometric cross-reference only, not contact, support, pressure, force, friction, slip, balance, tissue safety or an anatomical joint-centre measurement.",
              "", "## Foot-plant solve residuals", "",
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
              "Toe controls remain observed even when their local delta is zero; no multisegment foot anatomy is inferred.",
              "", "## Corrective return-to-neutral lifecycle", "",
              "The frozen benchmark resets the skeletal matrix basis after its final sample. The first row is captured before neutral driver refresh; the second follows one unchanged driver call at neutral.", "",
              "| Stage | skeletal basis neutral | residual controls | max translation control / mm | active shape keys | changed vertices vs sample 0 | max / RMS displacement mm |",
              "|:---|:---:|---:|:---|---:|---:|---:|"]
    for stage in data["corrective_return_to_neutral"]["stages"]:
        shape = stage["shape_keys"]
        geometry = stage["evaluated_geometry_vs_sample0"]
        lines.append(
            f"| {stage['stage']} | "
            f"{stage['skeletal_basis']['all_matrix_basis_identity_within_tolerance']} | "
            f"{len(stage['skeletal_basis']['controls_over_identity_tolerance'])} | "
            f"{stage['skeletal_basis']['max_translation_control']} / "
            f"{stage['skeletal_basis']['max_matrix_basis_translation_mm']:.9f} | "
            f"{len(shape['nonzero_keys'])} | "
            f"{geometry['changed_vertex_count_over_1e-6_mm']} / {geometry['vertex_count']} | "
            f"{geometry['max_displacement_mm']:.6f} / {geometry['rms_displacement_mm']:.6f} |")
    repeat = data["corrective_return_to_neutral"]["repeat_refresh_comparison"]
    repeat_geometry = repeat["evaluated_geometry_first_to_second"]
    lines += ["", "## Repeated neutral driver refresh", "",
              f"Skeletal fingerprint equal: **{repeat['skeletal_control_state_sha256_equal']}**; shape-key fingerprint equal: **{repeat['shape_key_all_values_sha256_equal']}**.",
              f"First-to-second refresh geometry: {repeat_geometry['changed_vertex_count_over_1e-6_mm']} / {repeat_geometry['vertex_count']} vertices above 0.000001 mm; max {repeat_geometry['max_displacement_mm']:.9f} mm; RMS {repeat_geometry['rms_displacement_mm']:.9f} mm.",
              "", "This separates skeletal cleanup from corrective-state cleanup. It does not establish anatomical neutral, deformation quality, contact, balance or tissue safety.", ""]
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
    sample0_vertices = []
    sample0_shape_keys = []
    correction.build_corrected_scene = lambda: result

    def tracked_plant_feet(loaded_rig, rest_heads):
        pre, post = run_tracked_plant_solve(
            loaded_rig, rest_heads, bpy.context.view_layer.update,
            original_plant_feet)
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
            "foot_skin_lower_envelope": {
                "status": "DESCRIPTIVE_EVALUATED_FOOT_SKIN_LOWER_ENVELOPE_NOT_CONTACT",
                "contact_claimed": False,
                "sides": {
                    side: foot_skin_lower_envelope(
                        V, dom, side, rig.matrix_world @ bones[f"foot_{side}"].head)
                    for side in ("l", "r")
                },
            },
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
        if sample == 0:
            sample0_vertices.extend(vector3(vertex) for vertex in V)
            sample0_shape_keys.append(shape_key_state(body.data.shape_keys.key_blocks))
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
    if len(sample0_shape_keys) != 1 or not sample0_vertices:
        raise ValueError("Missing sample-0 return reference")

    def return_stage(label, refresh_count):
        bpy.context.view_layer.update()
        vertices, _ = bench._evaluated(body)
        points = [vector3(vertex) for vertex in vertices]
        return {
            "stage": label,
            "neutral_driver_refresh_applied": refresh_count > 0,
            "neutral_driver_refresh_count": refresh_count,
            "skeletal_basis": skeletal_basis_state(rig.pose.bones),
            "shape_keys": shape_key_state(body.data.shape_keys.key_blocks),
            "evaluated_geometry_vs_sample0": geometry_delta_summary(
                sample0_vertices, points),
        }, points

    before_neutral_driver, _ = return_stage(
        "AFTER_BENCHMARK_SKELETAL_RESET_BEFORE_NEUTRAL_DRIVER_REFRESH", 0)
    drives.drive(rig, body)
    after_neutral_driver, first_refresh_vertices = return_stage(
        "AFTER_NEUTRAL_DRIVER_REFRESH", 1)
    drives.drive(rig, body)
    after_second_neutral_driver, second_refresh_vertices = return_stage(
        "AFTER_SECOND_NEUTRAL_DRIVER_REFRESH", 2)
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
        "skin_control_relative_motion": skin_control_relative_motion(captures),
        "corrective_return_to_neutral": {
            "status": "DESCRIPTIVE_SKELETAL_RESET_CORRECTIVE_LIFECYCLE_NOT_ANATOMY",
            "anatomical_approval": "NOT_GRANTED",
            "tissue_safety_claimed": False,
            "sample0_reference": {
                "sample": 0,
                "shape_keys": sample0_shape_keys[0],
            },
            "stages": [before_neutral_driver, after_neutral_driver,
                       after_second_neutral_driver],
            "repeat_refresh_comparison": {
                "status": "DESCRIPTIVE_REPEAT_NEUTRAL_DRIVER_IDEMPOTENCE_NOT_ANATOMY",
                "first_refresh_count": 1,
                "second_refresh_count": 2,
                "skeletal_control_state_sha256_equal": (
                    after_neutral_driver["skeletal_basis"]["control_state_sha256"] ==
                    after_second_neutral_driver["skeletal_basis"]["control_state_sha256"]),
                "shape_key_all_values_sha256_equal": (
                    after_neutral_driver["shape_keys"]["all_values_sha256"] ==
                    after_second_neutral_driver["shape_keys"]["all_values_sha256"]),
                "evaluated_geometry_first_to_second": geometry_delta_summary(
                    first_refresh_vertices, second_refresh_vertices),
            },
        },
        "limitations": [
            "Authored FK controls and world-space control trajectories are not ISB joint-coordinate measurements",
            "Bone heads are authored rig locations, not independently verified anatomical joint centres",
            "The benchmark foot solve and lowest evaluated vertex do not prove pressure, balance or ground contact",
            "Pre/post solve residuals expose authored root-correction behavior, not anatomical foot planting",
            "Foot/toe-dominant lower-envelope skin samples are descriptive geometry, not contact patches",
            "The single foot and toe controls do not establish talus, calcaneus or multisegment foot coordination",
            CORRECTIVE_RETURN_LIMITATION,
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

