"""Read-only evaluated surface-quality capture for ORIGINAL-v1 Phase 6.

Captures evaluated body topology, normals and self-intersection evidence from the
exact candidate. It never saves the Blend, repairs geometry, changes modifiers,
authors joint-support landmarks, or infers a Phase 6 PASS.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import math
from pathlib import Path
import subprocess
import sys

import bpy
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from original_v1_garment_evidence import capture
from original_v1_production_control import digest, ensure_finite

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(args) != 1:
    raise SystemExit("STOP — usage: blender ... --python scripts/capture_original_v1_surface_quality_blender.py -- <fresh-output.json>")
out = Path(args[0])
if out.exists():
    raise SystemExit("STOP — output already exists")

try:
    raw = capture(bpy, "body")
    body = bpy.data.objects.get("HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE")
    if body is None or body.type != "MESH":
        raise ValueError("owned ORIGINAL-v1 body mesh missing")
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
    try:
        mw = evaluated.matrix_world.copy()
        vertices_world = [mw @ v.co for v in mesh.vertices]
        faces = [tuple(p.vertices) for p in mesh.polygons]
        face_sets = [set(f) for f in faces]
        if not vertices_world or not faces:
            raise ValueError("evaluated body mesh is empty")

        tree = BVHTree.FromPolygons(vertices_world, faces)
        overlaps = sorted(
            (a, b)
            for a, b in tree.overlap(tree)
            if a < b and not (face_sets[a] & face_sets[b])
        )

        normal_matrix = mw.to_3x3().inverted_safe().transposed()
        polygon_normal_lengths = []
        invalid_polygon_normals = []
        for poly in mesh.polygons:
            n = normal_matrix @ poly.normal
            length = float(n.length)
            polygon_normal_lengths.append(length)
            if not math.isfinite(length) or length <= 1e-12:
                invalid_polygon_normals.append(poly.index)

        vertex_normal_lengths = []
        invalid_vertex_normals = []
        for vertex in mesh.vertices:
            n = normal_matrix @ vertex.normal
            length = float(n.length)
            vertex_normal_lengths.append(length)
            if not math.isfinite(length) or length <= 1e-12:
                invalid_vertex_normals.append(vertex.index)

        has_custom = getattr(mesh, "has_custom_normals", None)
        custom_state = "UNAVAILABLE_IN_THIS_BLENDER_API" if has_custom is None else bool(has_custom)

        modifiers = []
        for m in body.modifiers:
            modifiers.append({
                "name": m.name,
                "type": m.type,
                "show_viewport": bool(m.show_viewport),
                "show_render": bool(m.show_render),
            })

        result = {
            "schema_version": 1,
            "status": "EVIDENCE_ONLY",
            "phase_complete": False,
            "production_approved": False,
            "candidate_sha256": raw["candidate_sha256"],
            "source_candidate": raw["source_candidate"],
            "rig_id": raw["rig_id"],
            "blender_version": bpy.app.version_string,
            "body_object": body.name,
            "evaluated": {
                "vertex_count": len(mesh.vertices),
                "face_count": len(mesh.polygons),
                "loop_count": len(mesh.loops),
                "modifier_stack": modifiers,
            },
            "normals": {
                "custom_normals_state": custom_state,
                "invalid_polygon_normal_ids": invalid_polygon_normals,
                "invalid_vertex_normal_ids": invalid_vertex_normals,
                "polygon_normal_length_min": min(polygon_normal_lengths, default=None),
                "polygon_normal_length_max": max(polygon_normal_lengths, default=None),
                "vertex_normal_length_min": min(vertex_normal_lengths, default=None),
                "vertex_normal_length_max": max(vertex_normal_lengths, default=None),
                "note": "Finite/nonzero evaluated normal evidence only. This does not judge visual shading quality or approve intentional sharp/split-normal design.",
            },
            "self_intersection": {
                "method": "Blender BVHTree evaluated-surface overlap; face pairs sharing any evaluated vertex excluded",
                "intersecting_face_pair_count": len(overlaps),
                "intersecting_face_pairs": [list(pair) for pair in overlaps],
                "note": "Raw exact evaluated face-pair evidence. Contact/adjacency classification is separate; zero pairs is not by itself Phase 6 completion.",
            },
            "raw_body_snapshot_identity": {
                "candidate_sha256": raw["candidate_sha256"],
                "raw_vertex_count": len(raw["vertices"]),
                "raw_face_count": len(raw["faces"]),
                "snapshot_script_sha256": raw["snapshot_script_sha256"],
                "snapshot_helper_sha256": raw["snapshot_helper_sha256"],
            },
            "source_candidate_manifest": raw["source_candidate_manifest"],
            "capture_script": {
                "path": "scripts/capture_original_v1_surface_quality_blender.py",
                "sha256": digest(ROOT / "scripts/capture_original_v1_surface_quality_blender.py"),
            },
            "source_git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "capture_command": list(sys.argv),
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "unresolved_domain_checks": [
                "authored_joint_support_landmarks",
                "loaded_joint_support_views",
                "owner_surface_review",
                "classified_intentional_intersections_if_any",
            ],
        }
        ensure_finite(result)
    finally:
        evaluated.to_mesh_clear()

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(result, indent=2) + "\n")
    print("PHASE 6 SURFACE QUALITY EVIDENCE WRITTEN — EVIDENCE_ONLY")
except (OSError, ValueError, KeyError, TypeError, ArithmeticError, subprocess.SubprocessError) as exc:
    raise SystemExit("STOP — " + str(exc))
