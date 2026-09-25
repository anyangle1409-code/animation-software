"""Create a temporary export-ready V15 Blend without changing the editable candidate.

Repairs only genuinely new V15 vertices:
- resolves duplicate/default v15_baseline_vertex_id values;
- fills missing/non-normalized DEF-* weights from nearest V13e triangle;
- fills missing/zero/non-finite UV0/UV1 from nearest V13e triangle;
- triangulates an export-only copy.

Established V13e vertices keep their existing UVs and deform rows.
"""
from __future__ import annotations

import bpy
import bmesh
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v13e_fingertip_retopology.blend"
SOURCE = ROOT / "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v15a_deep_hand_rebuild.blend"
OUT = ROOT / "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v15a_deep_hand_rebuild_EXPORT.blend"
REPORT = ROOT / "reports" / "prepare_v15a_export_blender.json"

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if args:
    source = Path(args[0]).resolve()
else:
    source = SOURCE
if len(args) > 1:
    out = Path(args[1]).resolve()
else:
    out = OUT

for p in (BASE, source):
    if not p.is_file():
        raise SystemExit(f"Missing required Blend: {p}")
if out.resolve() == source.resolve() or out.resolve() == BASE.resolve():
    raise SystemExit("Export prep must write a separate temporary Blend")

def barycentric(p, a, b, c):
    v0, v1, v2 = b - a, c - a, p - a
    d00, d01, d11 = v0.dot(v0), v0.dot(v1), v1.dot(v1)
    d20, d21 = v2.dot(v0), v2.dot(v1)
    den = d00 * d11 - d01 * d01
    if abs(den) < 1e-18:
        return (1.0, 0.0, 0.0)
    vb = (d11 * d20 - d01 * d21) / den
    vc = (d00 * d21 - d01 * d20) / den
    va = 1.0 - vb - vc
    values = [max(0.0, float(va)), max(0.0, float(vb)), max(0.0, float(vc))]
    total = sum(values)
    if total <= 1e-12:
        return (1.0, 0.0, 0.0)
    return tuple(x / total for x in values)

# ---- V13e source surface -----------------------------------------------------
bpy.ops.wm.open_mainfile(filepath=str(BASE))
base_body = bpy.data.objects["Mike_Freeman"]
base_mesh = base_body.data
if any(len(p.vertices) != 3 for p in base_mesh.polygons):
    raise RuntimeError("V13e baseline is expected to be triangular")

base_positions = [v.co.copy() for v in base_mesh.vertices]
base_faces = [tuple(p.vertices) for p in base_mesh.polygons]
base_group_names = {g.index: g.name for g in base_body.vertex_groups}
base_bone_groups = {
    g.index: g.name for g in base_body.vertex_groups if g.name.startswith("DEF-")
}
base_weights = []
for v in base_mesh.vertices:
    row = {}
    for item in v.groups:
        name = base_bone_groups.get(item.group)
        if name is not None and item.weight:
            row[name] = float(item.weight)
    base_weights.append(row)

uv_layer_count = len(base_mesh.uv_layers)
if uv_layer_count < 2:
    raise RuntimeError("Expected V13e UV0 and UV1")
base_face_uv = []
for poly in base_mesh.polygons:
    per_layer = []
    for layer in base_mesh.uv_layers[:2]:
        per_layer.append([
            layer.data[li].uv.copy()
            for li in poly.loop_indices
        ])
    base_face_uv.append(per_layer)

tree = BVHTree.FromPolygons(base_positions, base_faces, all_triangles=True)

# ---- Candidate ---------------------------------------------------------------
bpy.ops.wm.open_mainfile(filepath=str(source))
body = bpy.data.objects["Mike_Freeman"]
mesh = body.data
before_positions = [v.co.copy() for v in mesh.vertices]

track = mesh.attributes.get("v15_baseline_vertex_id")
if track is None or track.domain != "POINT":
    raise RuntimeError("V15 candidate is missing v15_baseline_vertex_id; recreate it with prepare_v15_deep_hand_blender.py")
baseline_count = int(body.get("v15_baseline_vertex_count", 0))
if baseline_count != len(base_positions):
    raise RuntimeError(f"V15 baseline count mismatch: {baseline_count} vs {len(base_positions)}")

ids = [int(x.value) for x in track.data]
locations = defaultdict(list)
for i, value in enumerate(ids):
    if value > 0:
        locations[value].append(i)

# Resolve duplicate IDs that may have been copied/interpolated onto new geometry.
# The established V13e vertex is the duplicate closest to that ID's V13e position.
duplicate_reset = 0
for value, verts in list(locations.items()):
    if value < 1 or value > baseline_count:
        for vi in verts:
            track.data[vi].value = 0
            ids[vi] = 0
            duplicate_reset += 1
        continue
    if len(verts) <= 1:
        continue
    target = base_positions[value - 1]
    keep = min(verts, key=lambda vi: (mesh.vertices[vi].co - target).length)
    for vi in verts:
        if vi != keep:
            track.data[vi].value = 0
            ids[vi] = 0
            duplicate_reset += 1

ids = [int(x.value) for x in track.data]
present = {x for x in ids if x > 0}
missing = [i for i in range(1, baseline_count + 1) if i not in present]
if missing:
    raise RuntimeError(f"V15 lost {len(missing)} V13e baseline vertex IDs; first: {missing[:20]}")
duplicates = [x for x, count in __import__("collections").Counter(x for x in ids if x > 0).items() if count > 1]
if duplicates:
    raise RuntimeError(f"Duplicate V15 baseline IDs remain: {duplicates[:20]}")

new_vertices = [i for i, value in enumerate(ids) if value <= 0]

candidate_group_by_name = {g.name: g for g in body.vertex_groups}
for name in set(base_bone_groups.values()):
    if name not in candidate_group_by_name:
        candidate_group_by_name[name] = body.vertex_groups.new(name=name)

candidate_group_names = {g.index: g.name for g in body.vertex_groups}
candidate_bone_group_indices = {
    g.index for g in body.vertex_groups if g.name.startswith("DEF-")
}

nearest = {}
max_nearest_mm = 0.0
for vi in new_vertices:
    p = mesh.vertices[vi].co
    hit = tree.find_nearest(p)
    if hit is None:
        raise RuntimeError(f"No V13e surface match for new vertex {vi}")
    co, _normal, face_index, distance = hit
    if distance is None or face_index is None:
        raise RuntimeError(f"Incomplete V13e surface match for new vertex {vi}")
    max_nearest_mm = max(max_nearest_mm, float(distance) * 1000.0)
    if distance > 0.012:
        raise RuntimeError(f"New vertex {vi} is {distance*1000:.2f} mm from V13e surface; outside repair envelope")
    ia, ib, ic = base_faces[face_index]
    coeff = barycentric(co, base_positions[ia], base_positions[ib], base_positions[ic])
    nearest[vi] = (face_index, (ia, ib, ic), coeff)

# Repair only missing/bad DEF weights on genuinely new vertices.
repaired_weights = 0
for vi in new_vertices:
    v = mesh.vertices[vi]
    current = {
        candidate_group_names[item.group]: float(item.weight)
        for item in v.groups
        if item.group in candidate_bone_group_indices and item.weight
    }
    total = sum(current.values())
    if current and abs(total - 1.0) <= 1e-4:
        continue
    face_index, face, coeff = nearest[vi]
    merged = defaultdict(float)
    for src, factor in zip(face, coeff):
        for name, weight in base_weights[src].items():
            merged[name] += weight * factor
    norm = sum(merged.values())
    if norm <= 1e-12:
        raise RuntimeError(f"Could not interpolate weights for new vertex {vi}")
    # Remove only DEF weights, leaving V15 diagnostic groups intact.
    for item in list(v.groups):
        name = candidate_group_names.get(item.group, "")
        if name.startswith("DEF-"):
            candidate_group_by_name[name].remove([vi])
    for name, weight in merged.items():
        if weight > 1e-8:
            candidate_group_by_name[name].add([vi], weight / norm, "REPLACE")
    repaired_weights += 1

# Repair UVs only when a new vertex has non-finite or effectively zero UVs.
if len(mesh.uv_layers) < 2:
    raise RuntimeError("V15 candidate lost UV0/UV1")
new_set = set(new_vertices)
repaired_uv_loops = 0
for poly in mesh.polygons:
    for loop_index in poly.loop_indices:
        vi = mesh.loops[loop_index].vertex_index
        if vi not in new_set:
            continue
        needs = False
        for layer in mesh.uv_layers[:2]:
            uv = layer.data[loop_index].uv
            if not (math.isfinite(uv.x) and math.isfinite(uv.y)) or (abs(uv.x) < 1e-9 and abs(uv.y) < 1e-9):
                needs = True
        if not needs:
            continue
        face_index, face, coeff = nearest[vi]
        for layer_index, layer in enumerate(mesh.uv_layers[:2]):
            source_uv = base_face_uv[face_index][layer_index]
            uv = source_uv[0] * coeff[0] + source_uv[1] * coeff[1] + source_uv[2] * coeff[2]
            layer.data[loop_index].uv = uv
        repaired_uv_loops += 1

# Triangulate only the temporary export copy.
nontri_before = sum(len(p.vertices) != 3 for p in mesh.polygons)
if nontri_before:
    bm = bmesh.new()
    bm.from_mesh(mesh)
    faces = [f for f in bm.faces if len(f.verts) > 3]
    if faces:
        bmesh.ops.triangulate(bm, faces=faces)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
nontri_after = sum(len(p.vertices) != 3 for p in mesh.polygons)
if nontri_after:
    raise RuntimeError(f"Export copy still has {nontri_after} non-triangular faces")

after_positions = [v.co.copy() for v in mesh.vertices]
if len(after_positions) != len(before_positions):
    raise RuntimeError("Export prep unexpectedly changed vertex count")
max_move = max(((a - b).length for a, b in zip(after_positions, before_positions)), default=0.0)
if max_move > 1e-9:
    raise RuntimeError(f"Export prep changed geometry by {max_move*1000:.9f} mm")

bpy.context.preferences.filepaths.save_version = 0
out.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out))

report = {
    "source": source.name,
    "output": out.name,
    "baseline": BASE.name,
    "baseline_vertices_tracked": baseline_count,
    "new_v15_vertices": len(new_vertices),
    "duplicate_tracking_ids_reset_to_new": duplicate_reset,
    "repaired_weight_vertices": repaired_weights,
    "repaired_uv_loops": repaired_uv_loops,
    "new_vertex_max_nearest_v13e_mm": max_nearest_mm,
    "nontri_faces_before": nontri_before,
    "nontri_faces_after": nontri_after,
    "geometry_max_move_mm": max_move * 1000.0,
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(report, indent=2))
print("V15_EXPORT_PREP", json.dumps(report, indent=2), flush=True)
