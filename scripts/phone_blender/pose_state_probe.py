"""READ ONLY: measure actual in-memory W8 shoulder press S1/S5/S7 and cap.

This runs the original frozen r57 pose/drive code on a SHA-pinned W8
reconstruction without saving any .blend. The resulting driver state is
observed, not corrected. No anatomy, archive equivalence or motion approval.
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
KEY_PREFIXES = ("HGPT_S1_SHOULDER_", "HGPT_S2_FOLD_", "HGPT_S3_SHAPE_",
                "HGPT_S4_SCULPT_", "HGPT_S5_BAKE_", "HGPT_S6_RELAX_", "HGPT_S7_DELT_",
                "HGPT_C1_ARMTRUNK_", "HGPT_K1_ELBOW_")

def digest(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()

def finite(x):
    v = float(x)
    if not math.isfinite(v):
        raise ValueError("Nonfinite numerical pose state")
    return v

def q_angle_deg(quaternion):
    """Pose-bone local delta from quaternion, not absolute anatomical joint rotation."""
    q = quaternion.copy()
    q.normalize()
    return math.degrees(q.angle)

def shape_key_state(body, side):
    keys = body.data.shape_keys.key_blocks
    result = []
    for key in keys:
        if not any(key.name.startswith(prefix + side + "_") for prefix in KEY_PREFIXES):
            continue
        value = finite(key.value)
        if not -1e-6 <= value <= 1.000001:
            raise ValueError("Unexpected key value outside 0..1: " + key.name)
        result.append({"name": key.name, "actual_value": round(value, 6)})
    return sorted(result, key=lambda x: x["name"])


def vertex_residual_summary(reference_vertices, observed_vertices):
    if len(reference_vertices) != len(observed_vertices) or not reference_vertices:
        raise ValueError("return-state vertex count changed or empty")
    squared = []
    for start, observed in zip(reference_vertices, observed_vertices):
        if len(start) != 3 or len(observed) != 3:
            raise ValueError("return-state vertices must be 3D")
        delta = tuple(finite(b) - finite(a) for a, b in zip(start, observed))
        squared.append(sum(v * v for v in delta))
    return {
        "vertex_count": len(squared),
        "max_vertex_displacement_m": math.sqrt(max(squared)),
        "rms_vertex_displacement_m": math.sqrt(sum(squared) / len(squared)),
        "vertices_moved_gt_1e_9_m": sum(d > 1e-18 for d in squared),
    }


def return_state_summary(reference_vertices, returned_vertices, active_keys,
                         skeletal_pose_signature_restored_exactly):
    residual = vertex_residual_summary(reference_vertices, returned_vertices)
    keys = []
    for key in active_keys:
        name = key.get("name")
        value = finite(key.get("actual_value"))
        if not isinstance(name, str) or not name:
            raise ValueError("invalid active nonbasis shape key")
        keys.append({"name": name, "actual_value": value})
    keys.sort(key=lambda row: row["name"])
    maximum = residual["max_vertex_displacement_m"]
    pose_restored = skeletal_pose_signature_restored_exactly is True
    exact = maximum == 0.0 and not keys and pose_restored
    return {
        "status": "MEASURED_RUNTIME_RETURN_NOT_ANATOMICAL_NEUTRAL",
        "anatomical_neutral_claimed": False,
        "runtime_state_restored_exactly": exact,
        **residual,
        "active_nonbasis_shape_keys": keys,
        "skeletal_pose_signature_restored_exactly": pose_restored,
    }


def explicit_clear_summary(reference_vertices, returned_vertices, active_keys,
                           skeletal_pose_signature_restored_exactly):
    result = return_state_summary(reference_vertices, returned_vertices, active_keys,
                                  skeletal_pose_signature_restored_exactly)
    result["status"] = "EXPLICIT_IN_MEMORY_CLEAR_EXPERIMENT_NOT_MODEL_REPAIR"
    result["model_repair_claimed"] = False
    return result


def reverse_trajectory_summary(forward_vertices_by_sample, reverse_vertices_by_sample):
    expected = set(range(9))
    if set(forward_vertices_by_sample) != expected or set(reverse_vertices_by_sample) != expected:
        raise ValueError("reverse trajectory requires samples 0 through 8")
    rows = []
    for sample in range(8, -1, -1):
        rows.append({"sample": sample, **vertex_residual_summary(
            forward_vertices_by_sample[sample], reverse_vertices_by_sample[sample])})
    return {
        "status": "MEASURED_REVERSE_REPLAY_NOT_PHYSIOLOGICAL_RETURN",
        "physiological_return_claimed": False,
        "retraced_forward_samples_exactly": all(
            row["max_vertex_displacement_m"] == 0.0 for row in rows),
        "samples": rows,
    }


def valid_residual(row):
    if not isinstance(row, dict):
        return False
    maximum = row.get("max_vertex_displacement_m")
    rms = row.get("rms_vertex_displacement_m")
    moved = row.get("vertices_moved_gt_1e_9_m")
    count = row.get("vertex_count")
    return (
        type(maximum) in (int, float) and type(rms) in (int, float)
        and math.isfinite(maximum) and math.isfinite(rms)
        and 0 <= rms <= maximum
        and type(moved) is int and type(count) is int and count > 0
        and 0 <= moved <= count
        and not (maximum == 0.0 and (rms != 0.0 or moved != 0))
        and not (rms == 0.0 and maximum != 0.0)
        and (moved > 0) == (maximum > 1e-9))


def valid_active_nonbasis_keys(active):
    if not isinstance(active, list) or not all(isinstance(row, dict) for row in active):
        return False
    names = [row.get("name") for row in active]
    return (
        len(set(names)) == len(names)
        and all(isinstance(row.get("name"), str) and row["name"]
                and type(row.get("actual_value")) in (int, float)
                and math.isfinite(row["actual_value"])
                and row["actual_value"] != 0.0 for row in active))

def recorded_pose(rig, body, drives, sample, target_elevation):
    snapshot = {"sample": sample, "t": round(sample / 8.0, 4),
                "authored_press_ht_target_deg_NOT_measured": round(target_elevation, 5),
                "sides": {}}
    for side in ("l", "r"):
        measured = finite(drives.elevation_deg(rig, side))
        cap_name = "shoulder_cap_" + side
        cap = rig.pose.bones.get(cap_name)
        axilla_name = "axilla_" + side
        axilla = rig.pose.bones.get(axilla_name)
        snapshot["sides"][side] = {
            "humerothoracic_elevation_measured_by_pinned_driver_deg": round(measured, 5),
            "target_minus_driver_measurement_deg": round(target_elevation - measured, 5),
            "cap_helper_present": cap is not None,
            "cap_local_delta_angle_deg_not_absolute": round(q_angle_deg(cap.rotation_quaternion), 5) if cap and cap.rotation_mode == "QUATERNION" else None,
            "cap_pose_rotation_mode": cap.rotation_mode if cap else None,
            "axilla_helper_present": axilla is not None,
            "axilla_local_delta_angle_deg_not_absolute": round(q_angle_deg(axilla.rotation_quaternion), 5) if axilla and axilla.rotation_mode == "QUATERNION" else None,
            "actual_shape_key_values": shape_key_state(body, side),
        }
    return snapshot

def validate_report(data):
    errors = []
    if data.get("status") != "READ_ONLY_IN_MEMORY_POSE_STATE_ANATOMY_NOT_APPROVED":
        errors.append("unapproved diagnostic status")
    if data.get("model") != "W8" or data.get("source_sha256") != W8_SHA256:
        errors.append("unrecognised immutable source")
    if data.get("saved_blend") is not False or data.get("source_unchanged") is not True:
        errors.append("source preservation not demonstrated")
    if data.get("anatomical_approval") != "NOT_GRANTED" or data.get("quality_approval") != "NOT_GRANTED":
        errors.append("unearned approval")
    returned = data.get("post_benchmark_return_to_start_state")
    valid_return = isinstance(returned, dict)
    if valid_return:
        numeric = (returned.get("max_vertex_displacement_m"),
                   returned.get("rms_vertex_displacement_m"))
        active = returned.get("active_nonbasis_shape_keys")
        active_valid = valid_active_nonbasis_keys(active)
        maximum, rms = numeric
        moved = returned.get("vertices_moved_gt_1e_9_m")
        metric_consistent = (
            type(maximum) in (int, float) and type(rms) in (int, float)
            and math.isfinite(maximum) and math.isfinite(rms)
            and 0 <= rms <= maximum
            and type(moved) is int
            and not (maximum == 0.0 and (rms != 0.0 or moved != 0))
            and not (rms == 0.0 and maximum != 0.0)
            and (moved > 0) == (maximum > 1e-9))
        expected_exact = (maximum == 0.0 and rms == 0.0 and moved == 0
                          and active == []
                          and returned.get("skeletal_pose_signature_restored_exactly") is True)
        valid_return = (
            returned.get("status") == "MEASURED_RUNTIME_RETURN_NOT_ANATOMICAL_NEUTRAL"
            and returned.get("anatomical_neutral_claimed") is False
            and isinstance(returned.get("runtime_state_restored_exactly"), bool)
            and returned.get("runtime_state_restored_exactly") is expected_exact
            and type(returned.get("vertex_count")) is int
            and returned.get("vertex_count", 0) > 0
            and metric_consistent
            and 0 <= moved <= returned.get("vertex_count", -1)
            and active_valid
            and isinstance(returned.get("skeletal_pose_signature_restored_exactly"), bool))
    if not valid_return:
        errors.append("invalid return-to-start evidence")
    reference_vertex_count = returned.get("vertex_count") if isinstance(returned, dict) else None
    reverse = data.get("reverse_press_trajectory")
    reverse_rows = reverse.get("samples") if isinstance(reverse, dict) else None
    valid_reverse = (
        isinstance(reverse, dict)
        and reverse.get("status") == "MEASURED_REVERSE_REPLAY_NOT_PHYSIOLOGICAL_RETURN"
        and reverse.get("physiological_return_claimed") is False
        and isinstance(reverse.get("retraced_forward_samples_exactly"), bool)
        and isinstance(reverse_rows, list)
        and all(type(row.get("sample")) is int for row in reverse_rows)
        and [row.get("sample") for row in reverse_rows] == list(range(8, -1, -1))
        and all(valid_residual(row) for row in reverse_rows)
        and all(row.get("vertex_count") == reference_vertex_count
                for row in reverse_rows)
        and reverse.get("retraced_forward_samples_exactly") is all(
            row.get("max_vertex_displacement_m") == 0.0 for row in reverse_rows))
    if not valid_reverse:
        errors.append("invalid reverse trajectory evidence")
    cleared = data.get("explicit_key_clear_experiment")
    valid_clear = isinstance(cleared, dict) and valid_residual(cleared)
    if valid_clear:
        active = cleared.get("active_nonbasis_shape_keys")
        expected_exact = (
            cleared.get("max_vertex_displacement_m") == 0.0
            and cleared.get("rms_vertex_displacement_m") == 0.0
            and cleared.get("vertices_moved_gt_1e_9_m") == 0
            and active == []
            and cleared.get("skeletal_pose_signature_restored_exactly") is True)
        valid_clear = (
            cleared.get("status") == "EXPLICIT_IN_MEMORY_CLEAR_EXPERIMENT_NOT_MODEL_REPAIR"
            and cleared.get("anatomical_neutral_claimed") is False
            and cleared.get("model_repair_claimed") is False
            and isinstance(cleared.get("runtime_state_restored_exactly"), bool)
            and cleared.get("runtime_state_restored_exactly") is expected_exact
            and valid_active_nonbasis_keys(active)
            and cleared.get("vertex_count") == reference_vertex_count
            and isinstance(cleared.get("skeletal_pose_signature_restored_exactly"), bool))
    if not valid_clear:
        errors.append("invalid explicit-clear evidence")
    rows = data.get("samples")
    if not isinstance(rows, list) or len(rows) != 9 or [r.get("sample") for r in rows] != list(range(9)):
        errors.append("nine exact pose samples required")
        return errors
    for row in rows:
        if not isinstance(row, dict) or set(row.get("sides", {})) != {"l", "r"}:
            errors.append("both runtime suffix sides required")
            continue
        target = row.get("authored_press_ht_target_deg_NOT_measured")
        if not isinstance(target, (int, float)) or not math.isfinite(target):
            errors.append("missing target angle")
        for side in ("l", "r"):
            r = row["sides"][side]
            e = r.get("humerothoracic_elevation_measured_by_pinned_driver_deg")
            if not isinstance(e, (int, float)) or not math.isfinite(e):
                errors.append("missing actual measured elevation")
            keys = r.get("actual_shape_key_values", [])
            names = [k.get("name") for k in keys]
            if not keys or len(set(names)) != len(names):
                errors.append("missing/duplicate shape keys")
            if not any(name.startswith("HGPT_S7_DELT_") for name in names):
                errors.append("missing S7 driver channel")
            if any((not isinstance(k.get("actual_value"), (int, float))
                    or not math.isfinite(k["actual_value"])
                    or not -1e-6 <= k["actual_value"] <= 1.000001) for k in keys):
                errors.append("invalid shape key activation")
    return errors

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--r57-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    a = parser.parse_args()
    sources = list(a.source_dir.rglob("*.blend"))
    if len(sources) != 1:
        raise ValueError("Exactly one preserved W8 blend expected, got " + str(sources))
    source = sources[0].resolve()
    if digest(source) != W8_SHA256:
        raise ValueError("W8 source hash mismatch")

    root = a.r57_root.resolve()
    sys.path[:0] = [str(root / "scripts"), str(root / "scripts" / "anatomy_fit"),
                    str(Path(__file__).resolve().parents[1] / "recovery_diagnostics"),
                    str(Path(__file__).resolve().parents[1] / "body_v2")]
    import bpy
    import diagnose_candidates_blender as adapter
    import build_original_movement_benchmarks_blender as bench
    import build_functional_shoulder_correction_blender as correction
    import original_v1_review_candidate_drives as drives
    import original_v1_press_extension as press_extension
    from fixed_measurement_triangles import freeze_evaluated
    from corrective_edge_isolation import (measure as isolate_edges, markdown as isolation_markdown,
                                           individual_summary, individual_markdown,
                                           adjacent_controls, EDGES)
    from native_control_views import selected_snapshot_condition, snapshot_filename
    import numpy as np

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

    # Use the same immutable rest tessellation and metric code as 39937882229.
    original_build = correction.build_corrected_scene
    original_eval = bench._evaluated
    original_metric = bench.frame_metrics
    captures = []
    forward_vertices_by_sample = {}
    neighborhood = [None]
    snapshot_dir = a.out.parent / '_phone-control-snapshots'
    snapshot_dir.mkdir(parents=True, exist_ok=False)
    index = [0]
    def native_triangles(ob):
        ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
        me = ev.to_mesh()
        try:
            me.calc_loop_triangles()
            return [tuple(t.vertices) for t in me.loop_triangles]
        finally:
            ev.to_mesh_clear()
    frozen_evaluated, tessellation = freeze_evaluated(original_eval, native_triangles)
    correction.build_corrected_scene = lambda: result

    reference_vertices = [None]
    benchmark_start_pose_signature = [None]

    def skeletal_pose_signature():
        return (tuple(float(x) for row in rig.matrix_world for x in row),
                tuple((bone.name, tuple(float(x) for row in bone.matrix for x in row),
                       tuple(float(x) for row in bone.matrix_basis for x in row))
                      for bone in rig.pose.bones))

    def tracked_evaluated(ob):
        vertices, faces = frozen_evaluated(ob)
        if reference_vertices[0] is None:
            reference_vertices[0] = [tuple(float(x) for x in vertex) for vertex in vertices]
            benchmark_start_pose_signature[0] = skeletal_pose_signature()
        return vertices, faces

    bench._evaluated = tracked_evaluated

    def refresh_keys():
        body.data.update()
        body.update_tag()
        bpy.context.view_layer.update()

    def capture(V0, V, F, dom, rest_floor):
        i = index[0]
        index[0] += 1
        forward_vertices_by_sample[i] = [tuple(float(x) for x in vertex) for vertex in V]
        metric = original_metric(V0, V, F, dom, rest_floor)
        target = bench.PRESS["ht_start"] + (bench.PRESS["ht_end"] - bench.PRESS["ht_start"]) * bench.smooth(i / 8)
        snapshot = recorded_pose(rig, body, drives, i, target)
        if neighborhood[0] is None:
            neighborhood[0] = adjacent_controls(F)
        control_edges = sorted({tuple(e) for group in neighborhood[0] for e in group['control_edges']})
        def save_snapshot(condition, vertices, faces):
            if selected_snapshot_condition(i, condition):
                np.savez_compressed(snapshot_dir / snapshot_filename(i, condition),
                                    vertices=np.asarray(vertices, dtype=np.float64),
                                    faces=np.asarray(faces, dtype=np.int64),
                                    focus_ids=sorted({v for edge in EDGES for v in edge}),
                                    source_sha256=W8_SHA256)
        snapshot["corrective_edge_isolation"] = isolate_edges(
            body, lambda: bench._evaluated(body), refresh_keys,
            skeletal_pose_signature, V0, V, F, edges=(*EDGES, *control_edges),
            snapshot_sink=save_snapshot)
        isolation = snapshot['corrective_edge_isolation']
        isolation['adjacent_control_selection'] = neighborhood[0]
        for edge in isolation['edges']:
            edge['edge_role'] = ('ranked_seed' if tuple(edge['vertex_ids']) in EDGES
                                 else 'adjacent_topology_control')
        snapshot["actual_native_deformation_metrics"] = {
            name: metric[name] for name in
            ("collapse_lt_0_1", "stretch_gt_2", "self_intersecting_pairs", "body_volume_change_pct")
        }
        captures.append(snapshot)
        print("READ_ONLY_POSE_CAPTURE", i, [snapshot["sides"][s]["humerothoracic_elevation_measured_by_pinned_driver_deg"] for s in ("l", "r")], flush=True)
        return metric

    bench.frame_metrics = capture
    try:
        outcome = bench.run(only=["shoulder_press"],
                            post_pose=lambda r: drives.drive(r["runtime"], r["body"]))
    finally:
        bench.frame_metrics = original_metric
        bench._evaluated = original_eval
        correction.build_corrected_scene = original_build
    bpy.context.view_layer.update()
    returned_vertices, _ = frozen_evaluated(body)
    active_keys = [
        {"name": key.name, "actual_value": finite(key.value)}
        for key in body.data.shape_keys.key_blocks[1:] if finite(key.value) != 0.0
    ]
    returned = return_state_summary(
        reference_vertices[0], returned_vertices, active_keys,
        benchmark_start_pose_signature[0] == skeletal_pose_signature())
    reverse_vertices_by_sample = {}
    for i in range(8, -1, -1):
        bench.pose_press(result, i / 8.0, correction)
        drives.drive(result["runtime"], result["body"])
        bpy.context.view_layer.update()
        vertices, _ = frozen_evaluated(body)
        reverse_vertices_by_sample[i] = [
            tuple(float(x) for x in vertex) for vertex in vertices]
        print("READ_ONLY_REVERSE_POSE_CAPTURE", i, flush=True)
    reverse = reverse_trajectory_summary(
        forward_vertices_by_sample, reverse_vertices_by_sample)

    bench._reset(rig)
    for key in body.data.shape_keys.key_blocks[1:]:
        key.value = 0.0
    refresh_keys()
    cleared_vertices, _ = frozen_evaluated(body)
    cleared_active_keys = [
        {"name": key.name, "actual_value": finite(key.value)}
        for key in body.data.shape_keys.key_blocks[1:] if finite(key.value) != 0.0
    ]
    cleared = explicit_clear_summary(
        reference_vertices[0], cleared_vertices, cleared_active_keys,
        benchmark_start_pose_signature[0] == skeletal_pose_signature())
    after = adapter.rest_signature(rig, body)
    unchanged = digest(source) == W8_SHA256
    if before != after or not unchanged:
        raise ValueError("Preserved source or in-memory rest bones changed")
    if len(captures) != 9 or len(outcome["benchmarks"]["shoulder_press"]["frames"]) != 9:
        raise ValueError("Incomplete benchmark run")
    data = {
        "status": "READ_ONLY_IN_MEMORY_POSE_STATE_ANATOMY_NOT_APPROVED",
        "model": "W8", "source_sha256": W8_SHA256,
        "pinned_r57_source_commit": R57_SHA,
        "rest_tessellation": tessellation,
        "rest_bone_signature_unchanged": True,
        "saved_blend": False, "source_unchanged": unchanged,
        "anatomical_approval": "NOT_GRANTED", "quality_approval": "NOT_GRANTED",
        "model_is_reconstruction_not_approved_original": True,
        "key_values_measured_after_actual_post_pose_driver_call": True,
        "post_benchmark_return_to_start_state": returned,
        "reverse_press_trajectory": reverse,
        "explicit_key_clear_experiment": cleared,
        "samples": captures,
        "limitations": [
            "Actual geometric pose/shape-key state, but actual angles still depend on project-authored shoulder rig assumptions",
            "Cap quaternion angle is local helper delta, not an anatomical joint rotation",
            "These are W8 candidate in-memory poses, not an authorized model repair",
            "Measured metrics describe current failed benchmark, never clinical exercise safety",
            "Return compares runtime state after the forward sweep with its benchmark start; it is not an anatomical neutral pose or a reverse trajectory",
            "Reverse replay only tests deterministic retracing of the same authored press parameter samples; it is not a physiological return trajectory",
            "Explicit skeletal reset plus zeroing all non-Basis keys is an isolated in-memory experiment, not a source edit or model repair",
            "No muscle anchors, ISB joint axes or anatomical left/right certified",
        ],
    }
    errors = validate_report(data)
    if errors:
        raise ValueError("Unusable read-only pose state report: " + "; ".join(errors))
    a.out.mkdir(parents=True, exist_ok=False)
    (a.out / "w8_shoulder_driver_pose_state.json").write_text(
        json.dumps(data, indent=2) + "\n", encoding="utf-8")
    (a.out / "w8_fixed_pose_corrective_edge_isolation.md").write_text(
        isolation_markdown(captures), encoding="utf-8")
    individual = individual_summary(captures)
    (a.out / "w8_individual_active_key_isolation.json").write_text(
        json.dumps(individual, indent=2) + "\n", encoding="utf-8")
    (a.out / "w8_individual_active_key_isolation.md").write_text(
        individual_markdown(individual), encoding="utf-8")
    print("W8_SHOULDER_DRIVER_ACTUAL_POSE_STATE_WRITTEN", len(captures), flush=True)

if __name__ == "__main__":
    main()
