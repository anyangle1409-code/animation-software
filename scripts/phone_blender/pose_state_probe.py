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
    bench._evaluated, tessellation = freeze_evaluated(original_eval, native_triangles)
    correction.build_corrected_scene = lambda: result

    def skeletal_pose_signature():
        return (tuple(float(x) for row in rig.matrix_world for x in row),
                tuple((bone.name, tuple(float(x) for row in bone.matrix for x in row),
                       tuple(float(x) for row in bone.matrix_basis for x in row))
                      for bone in rig.pose.bones))

    def refresh_keys():
        body.data.update()
        body.update_tag()
        bpy.context.view_layer.update()

    def capture(V0, V, F, dom, rest_floor):
        i = index[0]
        index[0] += 1
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
        "samples": captures,
        "limitations": [
            "Actual geometric pose/shape-key state, but actual angles still depend on project-authored shoulder rig assumptions",
            "Cap quaternion angle is local helper delta, not an anatomical joint rotation",
            "These are W8 candidate in-memory poses, not an authorized model repair",
            "Measured metrics describe current failed benchmark, never clinical exercise safety",
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
