#!/usr/bin/env python3
"""Capture evaluated body/garment pose evidence and matched bare/dressed review renders.

Blender-only helper. It reuses the authoritative frozen stress-pose script via
runpy in metrics-only mode; it does not redefine poses, save the Blend, repair
geometry, infer acceptable contact, or approve a model phase.
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
from mathutils import Vector
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
sys.path.insert(0, str(ROOT / "scripts"))
from original_v1_locked_rig import load_locked_rig, blender_armature_issues
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


if not SOURCE.is_file() or not MANIFEST.is_file():
    raise SystemExit("saved candidate Blend and adjacent manifest required")
source_sha = digest(SOURCE)
source_manifest = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
if source_manifest.get("candidate") != SOURCE.name or source_manifest.get("candidate_sha256") != source_sha:
    raise SystemExit("candidate manifest identity differs from opened Blend")
if f"_{REVISION}.blend" not in SOURCE.name:
    raise SystemExit("requested revision does not match opened candidate filename")
if not bpy.context.scene.get("hgpt_not_production"):
    raise SystemExit("candidate-only scene required")

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
set_dressed = ns["set_dressed"]
scene = ns["scene"]
cam = ns["cam"]
cam_data = ns["cam_data"]
if shorts is None or shorts.type != "MESH":
    raise SystemExit("named candidate garment required; no body fallback")
locked_rig = load_locked_rig(ROOT)
rig_issues = blender_armature_issues(rig, locked_rig)
if rig_issues:
    raise SystemExit("locked rev2c rig required: " + "; ".join(rig_issues))
if body.find_armature() != rig or shorts.find_armature() != rig:
    raise SystemExit("body and garment must be bound to the same locked rev2c rig")

source_pose_report_path = pose_source_dir / "pose_test_report.json"
source_pose_manifest_path = pose_source_dir / "render_source_manifest.json"
source_pose_report = json.loads(source_pose_report_path.read_text(encoding="utf-8"))
source_pose_by_name = {row["pose"]: row for row in source_pose_report}
if set(source_pose_by_name) != set(poses):
    raise SystemExit("authoritative pose-source coverage differs")

DRESS_MASK = ns.get("DRESS_MASK")


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


def surface_metrics():
    set_clearance_evaluation()
    bverts, bfaces = evaluated_surface(body)
    gverts, gfaces = evaluated_surface(shorts)
    if not len(bverts) or not len(gverts) or not bfaces or not gfaces:
        raise RuntimeError("evaluated body/garment surface is empty")
    btree = BVHTree.FromPolygons([Vector(v.tolist()) for v in bverts], bfaces)
    gtree = BVHTree.FromPolygons([Vector(v.tolist()) for v in gverts], gfaces)
    overlaps = btree.overlap(gtree)
    bd = nearest_min_distance(bverts, gtree)
    gd = nearest_min_distance(gverts, btree)
    if bd is None or gd is None:
        raise RuntimeError("nearest-surface query failed")
    return {
        "body_vertex_count_evaluated": int(len(bverts)),
        "garment_vertex_count_evaluated": int(len(gverts)),
        "body_face_count_evaluated": int(len(bfaces)),
        "garment_face_count_evaluated": int(len(gfaces)),
        "body_garment_intersecting_face_pairs": int(len(overlaps)),
        "body_to_garment_min_vertex_surface_distance_mm": round(bd * 1000.0, 4),
        "garment_to_body_min_vertex_surface_distance_mm": round(gd * 1000.0, 4),
        "garment_lowest_z_mm": round(float(gverts[:, 2].min()) * 1000.0, 4),
        "garment_vertices_below_floor": int((gverts[:, 2] < -1e-6).sum()),
    }, bverts, gverts


def pose_state_hash() -> str:
    payload = []
    for p in sorted(rig.pose.bones, key=lambda x: x.name):
        payload.append({"name": p.name, "matrix": [[round(float(v), 9) for v in row] for row in p.matrix]})
    return hashlib.sha256(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()).hexdigest()


def apply_pose(name: str) -> None:
    reset()
    rig.location = (0, 0, 0)
    rig.rotation_euler = (0, 0, 0)
    upd()
    handle.clear()
    for obj in [o for o in bpy.data.objects if o.name.startswith("REVIEW_HANDLE")]:
        bpy.data.objects.remove(obj)
    poses[name]()
    upd()


REVIEW_SPECS = [
    ("neutral", "front", "full"),
    ("neutral", "rear", "full"),
    ("neutral", "side", "full"),
    ("neutral", "three_quarter", "full"),
    ("neutral", "waist_front", "waist"),
    ("neutral", "hem_front", "hem"),
    ("neutral", "seat_rear", "seat"),
    ("press_top", "three_quarter", "full"),
    ("squat_bottom", "three_quarter", "full"),
    ("squat_bottom", "waist_front", "waist"),
    ("lunge", "three_quarter", "full"),
    ("lunge", "waist_front", "waist"),
    ("pushup_bottom", "three_quarter", "full"),
    ("row", "three_quarter", "full"),
    ("curl_handle", "three_quarter", "full"),
    ("pullup_bar", "three_quarter", "full"),
]

VIEW_ANGLES = {"front": (0, 5), "rear": (180, 5), "side": (90, 5), "three_quarter": (35, 12)}


def direction_for(view: str) -> Vector:
    if view in VIEW_ANGLES:
        az, el = VIEW_ANGLES[view]
    elif view in ("waist_front", "hem_front"):
        az, el = 0, 5
    elif view == "seat_rear":
        az, el = 180, 5
    else:
        raise ValueError("unknown view")
    a, e = math.radians(az), math.radians(el)
    return Vector((-math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))


def camera_for(view: str, kind: str, bverts: np.ndarray, gverts: np.ndarray) -> dict:
    union = np.concatenate((bverts, gverts), axis=0)
    lo, hi = union.min(axis=0), union.max(axis=0)
    glo, ghi = gverts.min(axis=0), gverts.max(axis=0)
    if kind == "full":
        target = Vector(((lo + hi) / 2).tolist())
        scale = float(max(hi - lo)) * 1.12
    else:
        gmid = (glo + ghi) / 2
        gh = max(float(ghi[2] - glo[2]), 1e-6)
        gw = max(float(ghi[0] - glo[0]), 1e-6)
        if kind == "waist":
            target = Vector((float(gmid[0]), float(gmid[1]), float(ghi[2] - gh * 0.12)))
            scale = max(0.28, gw * 1.30)
        elif kind == "hem":
            target = Vector((float(gmid[0]), float(gmid[1]), float(glo[2] + gh * 0.16)))
            scale = max(0.30, gw * 1.25)
        elif kind == "seat":
            target = Vector((float(gmid[0]), float(ghi[1]), float(gmid[2])))
            scale = max(0.34, gw * 1.25)
        else:
            raise ValueError("unknown close-up kind")
    direction = direction_for(view)
    cam_data.ortho_scale = scale
    cam.location = target + direction * 8
    cam.rotation_mode = "QUATERNION"
    cam.rotation_quaternion = (-direction).to_track_quat("-Z", "Y")
    upd()
    return {
        "camera_matrix_world": [[round(float(v), 9) for v in row] for row in cam.matrix_world],
        "orthographic_scale": round(float(cam_data.ortho_scale), 9),
        "resolution": [scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage],
        "engine": scene.render.engine,
        "light_direction": [round(float(v), 9) for v in scene.display.light_direction],
        "shading_light": scene.display.shading.light,
        "shading_color_type": scene.display.shading.color_type,
        "shadows": bool(scene.display.shading.show_shadows),
        "shadow_intensity": round(float(scene.display.shading.shadow_intensity), 9),
        "cavity": bool(scene.display.shading.show_cavity),
    }


scene.render.image_settings.file_format = "PNG"
scene.render.resolution_percentage = 100
review_dir = OUT / "review"
review_dir.mkdir()
metrics_rows = []
for name in poses:
    apply_pose(name)
    metrics, _bverts, _gverts = surface_metrics()
    metrics_rows.append({
        "pose": name,
        "pose_state_sha256": pose_state_hash(),
        "source_body_metrics": source_pose_by_name[name],
        **metrics,
    })

render_rows = []
for pose, view, kind in REVIEW_SPECS:
    apply_pose(pose)
    _metrics, bverts, gverts = surface_metrics()
    capture_key = camera_for(view, kind, bverts, gverts)
    for presentation in ("bare", "dressed"):
        set_dressed(presentation == "dressed")
        upd()
        filename = f"{pose}_{view}_{presentation}.png"
        path = review_dir / filename
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        render_rows.append({
            "pose": pose, "view": view, "kind": kind, "presentation": presentation,
            "file": path.relative_to(OUT).as_posix(), "sha256": digest(path),
            "capture_key": capture_key,
        })
    set_clearance_evaluation()

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
    "evaluation": {
        "body_mask_disabled_for_clearance": DRESS_MASK is not None,
        "body_mask_name": DRESS_MASK.name if DRESS_MASK is not None else None,
        "note": "Full underlying body and garment are evaluated together. Intersection/clearance counts are raw evidence, not acceptable-contact classification.",
    },
    "poses": metrics_rows,
    "review": {"owner_review": "pending", "blocking": False, "matched_pairs": True, "files": render_rows},
    "unresolved_checks": [
        "legitimate_contact_classification",
        "continuous_dressed_motion",
        "full_modifier_shape_key_custom_normal_inventory",
        "garment_authoring_provenance",
        "production_clearance_gate",
        "owner_visual_acceptance",
    ],
    "limits": "Static frozen stress poses plus matched review captures only. No clearance threshold, hidden-skin exemption, repair permission, Phase 7 PASS or production approval is inferred.",
}
(OUT / "dressed_pose_evidence.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("DRESSED EVIDENCE CAPTURED — EVIDENCE_ONLY; owner review pending; no phase PASS")
