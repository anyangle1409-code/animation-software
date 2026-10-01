#!/usr/bin/env python3
"""Capture deterministic sampled ORIGINAL-v1 dressed movement-range evidence.

This Blender-only helper reuses the authoritative frozen stress-pose functions,
interpolates between declared waypoint states from ORIGINAL_V1_DRESSED_RANGE_PLAN.json,
and records raw body/garment/floor evidence. It never saves the Blend, changes a
pose definition, classifies contact, changes a gate, or approves a phase.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import runpy
import subprocess
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(ARGS) != 2:
    raise SystemExit("usage: -- <fresh_output_dir> <rN>")
OUT = Path(ARGS[0])
REVISION = ARGS[1]
if not REVISION.startswith("r") or not REVISION[1:].isdigit():
    raise SystemExit("numbered candidate revision required")
OUT.mkdir(parents=True, exist_ok=False)

ROOT = Path(__file__).resolve().parent.parent
PLAN_PATH = ROOT / "ORIGINAL_V1_DRESSED_RANGE_PLAN.json"
POSE_SCRIPT = ROOT / "scripts/pose_test_original_v1_o4_candidate_blender.py"
CAPTURE_SCRIPT = Path(__file__).resolve()
SOURCE = Path(bpy.data.filepath)
MANIFEST = SOURCE.with_suffix(".json")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


if not SOURCE.is_file() or not MANIFEST.is_file() or not PLAN_PATH.is_file():
    raise SystemExit("candidate Blend, adjacent manifest and range plan required")
source_sha = digest(SOURCE)
source_manifest = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
if source_manifest.get("candidate") != SOURCE.name or source_manifest.get("candidate_sha256") != source_sha:
    raise SystemExit("candidate manifest identity differs from opened Blend")
if f"_{REVISION}.blend" not in SOURCE.name:
    raise SystemExit("requested revision does not match opened candidate filename")
if not bpy.context.scene.get("hgpt_not_production"):
    raise SystemExit("candidate-only scene required")

plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
sample_count = plan.get("sample_policy", {}).get("samples_per_segment")
if type(sample_count) is not int or sample_count < 3:
    raise SystemExit("invalid samples_per_segment in range plan")
paths = plan.get("paths")
if not isinstance(paths, list) or not paths:
    raise SystemExit("range plan has no paths")

pose_source_dir = OUT / "pose_source"
old_argv = sys.argv[:]
try:
    sys.argv = [str(POSE_SCRIPT), "--", str(pose_source_dir), "", "--metrics-only"]
    ns = runpy.run_path(str(POSE_SCRIPT), run_name="__hgpt_pose_source__")
finally:
    sys.argv = old_argv

body = ns["body"]
shorts = ns["shorts"]
rig = ns["rig"]
poses = ns["POSES"]
reset = ns["reset"]
upd = ns["upd"]
handle = ns["HANDLE"]
DRESS_MASK = ns.get("DRESS_MASK")
if shorts is None or shorts.type != "MESH":
    raise SystemExit("named candidate garment required; no body fallback")
if rig.type != "ARMATURE" or len(rig.data.bones) != 63:
    raise SystemExit("canonical 63-bone rig required")
if body.find_armature() != rig or shorts.find_armature() != rig:
    raise SystemExit("body and garment must be bound to the same canonical rig")

declared_waypoints = {w for p in paths for w in p.get("waypoints", [])}
if not declared_waypoints or not declared_waypoints.issubset(poses):
    raise SystemExit("range plan references unknown authoritative waypoint")

source_pose_report_path = pose_source_dir / "pose_test_report.json"
source_pose_manifest_path = pose_source_dir / "render_source_manifest.json"
source_pose_report = json.loads(source_pose_report_path.read_text(encoding="utf-8"))
if {row["pose"] for row in source_pose_report} != set(poses):
    raise SystemExit("authoritative pose-source coverage differs")


def clear_handles() -> None:
    handle.clear()
    for obj in [o for o in bpy.data.objects if o.name.startswith("REVIEW_HANDLE")]:
        bpy.data.objects.remove(obj)


def apply_pose(name: str) -> None:
    reset()
    rig.location = (0, 0, 0)
    rig.rotation_mode = "XYZ"
    rig.rotation_euler = (0, 0, 0)
    rig.scale = (1, 1, 1)
    upd()
    clear_handles()
    poses[name]()
    upd()


def matrix_basis_state():
    return {
        p.name: [[float(v) for v in row] for row in p.matrix_basis]
        for p in rig.pose.bones
    }


def object_state():
    rig.rotation_mode = "QUATERNION"
    return {
        "location": list(rig.location),
        "rotation_quaternion": list(rig.rotation_quaternion),
        "scale": list(rig.scale),
    }


def endpoint_state(name: str) -> dict:
    apply_pose(name)
    return {"pose": name, "rig": object_state(), "bones": matrix_basis_state()}


endpoint_states = {name: endpoint_state(name) for name in sorted(declared_waypoints)}


def matrix_from_rows(rows):
    return Matrix(rows)


def lerp_matrix_basis(a, b, t: float) -> Matrix:
    ma, mb = matrix_from_rows(a), matrix_from_rows(b)
    la, qa, sa = ma.decompose()
    lb, qb, sb = mb.decompose()
    loc = la.lerp(lb, t)
    rot = qa.slerp(qb, t)
    scale = sa.lerp(sb, t)
    return Matrix.LocRotScale(loc, rot, scale)


def lerp_vec(a, b, t: float) -> Vector:
    return Vector(a).lerp(Vector(b), t)


def set_interpolated(a: dict, b: dict, t: float) -> None:
    reset()
    clear_handles()
    rig.location = lerp_vec(a["rig"]["location"], b["rig"]["location"], t)
    rig.rotation_mode = "QUATERNION"
    qa = Vector(a["rig"]["rotation_quaternion"][1:]).to_track_quat("X", "Y") if False else None
    # Quaternion constructor keeps stored [w, x, y, z] order explicit.
    from mathutils import Quaternion
    q0 = Quaternion(a["rig"]["rotation_quaternion"])
    q1 = Quaternion(b["rig"]["rotation_quaternion"])
    rig.rotation_quaternion = q0.slerp(q1, t)
    rig.scale = lerp_vec(a["rig"]["scale"], b["rig"]["scale"], t)
    for p in rig.pose.bones:
        p.matrix_basis = lerp_matrix_basis(a["bones"][p.name], b["bones"][p.name], t)
    upd()


def set_clearance_evaluation() -> None:
    if DRESS_MASK is not None:
        DRESS_MASK.show_viewport = False
        DRESS_MASK.show_render = False
    shorts.hide_viewport = False
    shorts.hide_render = False
    upd()


def evaluated_surface(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    mw = ev.matrix_world
    verts = np.array([(mw @ v.co)[:] for v in ev.data.vertices], dtype=float)
    faces = [tuple(p.vertices) for p in ev.data.polygons]
    return verts, faces


def nearest_min_distance(vertices: np.ndarray, tree: BVHTree) -> float | None:
    best = None
    for row in vertices:
        hit = tree.find_nearest(Vector(row.tolist()))
        if hit is None:
            continue
        dist = float(hit[3])
        if best is None or dist < best:
            best = dist
    return best


def pose_state_hash() -> str:
    payload = {
        "rig_location": [round(float(v), 9) for v in rig.location],
        "rig_rotation_quaternion": [round(float(v), 9) for v in rig.rotation_quaternion],
        "rig_scale": [round(float(v), 9) for v in rig.scale],
        "bones": [
            {"name": p.name, "basis": [[round(float(v), 9) for v in row] for row in p.matrix_basis]}
            for p in sorted(rig.pose.bones, key=lambda x: x.name)
        ],
    }
    return hashlib.sha256(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()).hexdigest()


def surface_metrics():
    set_clearance_evaluation()
    bverts, bfaces = evaluated_surface(body)
    gverts, gfaces = evaluated_surface(shorts)
    if not len(bverts) or not len(gverts) or not bfaces or not gfaces:
        raise RuntimeError("evaluated body/garment surface is empty")
    btree = BVHTree.FromPolygons([Vector(v.tolist()) for v in bverts], bfaces)
    gtree = BVHTree.FromPolygons([Vector(v.tolist()) for v in gverts], gfaces)
    overlaps = sorted((int(a), int(b)) for a, b in btree.overlap(gtree))
    bd = nearest_min_distance(bverts, gtree)
    gd = nearest_min_distance(gverts, btree)
    if bd is None or gd is None:
        raise RuntimeError("nearest-surface query failed")
    body_below = np.flatnonzero(bverts[:, 2] < -1e-6).astype(int).tolist()
    garment_below = np.flatnonzero(gverts[:, 2] < -1e-6).astype(int).tolist()
    body_floor_2mm = np.flatnonzero(np.abs(bverts[:, 2]) <= 0.002).astype(int).tolist()
    garment_floor_2mm = np.flatnonzero(np.abs(gverts[:, 2]) <= 0.002).astype(int).tolist()
    pair_bytes = json.dumps(overlaps, separators=(",", ":")).encode()
    return {
        "body_garment_intersecting_face_pairs": len(overlaps),
        "body_garment_face_pairs": overlaps,
        "body_garment_face_pairs_sha256": hashlib.sha256(pair_bytes).hexdigest(),
        "body_to_garment_min_vertex_surface_distance_mm": round(bd * 1000.0, 4),
        "garment_to_body_min_vertex_surface_distance_mm": round(gd * 1000.0, 4),
        "body_lowest_z_mm": round(float(bverts[:, 2].min()) * 1000.0, 4),
        "garment_lowest_z_mm": round(float(gverts[:, 2].min()) * 1000.0, 4),
        "body_vertices_below_floor": body_below,
        "garment_vertices_below_floor": garment_below,
        "body_vertices_within_2mm_floor": body_floor_2mm,
        "garment_vertices_within_2mm_floor": garment_floor_2mm,
    }


rows = []
for path in paths:
    path_id = path.get("id")
    waypoints = path.get("waypoints")
    if not isinstance(path_id, str) or not isinstance(waypoints, list) or len(waypoints) < 2:
        raise SystemExit("invalid movement path")
    path_sample = 0
    for segment_index in range(len(waypoints) - 1):
        start, end = waypoints[segment_index], waypoints[segment_index + 1]
        a, b = endpoint_states[start], endpoint_states[end]
        for i in range(sample_count):
            if segment_index > 0 and i == 0 and plan["sample_policy"].get("deduplicate_shared_waypoints"):
                continue
            t = i / (sample_count - 1)
            set_interpolated(a, b, t)
            metrics = surface_metrics()
            rows.append({
                "path_id": path_id,
                "path_sample_index": path_sample,
                "segment_index": segment_index,
                "segment_start": start,
                "segment_end": end,
                "segment_sample_index": i,
                "segment_t": round(t, 8),
                "pose_state_sha256": pose_state_hash(),
                **metrics,
            })
            path_sample += 1

report = {
    "schema_version": 1,
    "status": "EVIDENCE_ONLY",
    "phase_complete": False,
    "production_approved": False,
    "candidate_revision": REVISION,
    "candidate": SOURCE.name,
    "candidate_sha256": source_sha,
    "candidate_manifest": MANIFEST.name,
    "candidate_manifest_sha256": digest(MANIFEST),
    "rig_id": "hgpt_canonical_v4_original",
    "plan": PLAN_PATH.relative_to(ROOT).as_posix(),
    "plan_sha256": digest(PLAN_PATH),
    "source_pose_script": POSE_SCRIPT.relative_to(ROOT).as_posix(),
    "source_pose_script_sha256": digest(POSE_SCRIPT),
    "capture_script": CAPTURE_SCRIPT.relative_to(ROOT).as_posix(),
    "capture_script_sha256": digest(CAPTURE_SCRIPT),
    "source_pose_report": source_pose_report_path.relative_to(OUT).as_posix(),
    "source_pose_report_sha256": digest(source_pose_report_path),
    "source_pose_manifest": source_pose_manifest_path.relative_to(OUT).as_posix(),
    "source_pose_manifest_sha256": digest(source_pose_manifest_path),
    "source_git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
    "blender_version": bpy.app.version_string,
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "sample_policy": plan["sample_policy"],
    "interpolation": plan["interpolation"],
    "contact_scope": plan["contact_scope"],
    "paths": paths,
    "samples": rows,
    "classification_status": "UNCLASSIFIED",
    "unresolved_checks": [
        "per_sample_legitimate_contact_classification",
        "pushup_continuous_range",
        "continuous_equipment_contact",
        "adaptive_or_runtime_specific_refinement",
        "production_clearance_gate",
        "owner_visual_acceptance",
    ],
    "limits": "Finite deterministic model-range samples only. Raw intersections/floor findings are not classified or waived. This is not runtime biomechanics and does not prove unsampled intervals.",
}
(OUT / "dressed_range_evidence.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("DRESSED RANGE EVIDENCE CAPTURED — EVIDENCE_ONLY; contact classification remains open")
