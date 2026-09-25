"""Prepare a V15 diagnostic Blender copy from V13e without changing geometry.

Creates vertex groups that let Work immediately see protected push-up contact,
patch boundaries, sharp fold edges and the safe digit rebuild core.
"""
from __future__ import annotations

import bpy
import bmesh
import json
import math
import struct
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v13e_fingertip_retopology.blend"
OUT = ROOT / "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v15a_deep_hand_rebuild.blend"
REPORT = ROOT / "reports" / "prepare_v15a_deep_hand_rebuild.json"
V8_GLB = ROOT / "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy.glb"
CONTACT_REPORT = ROOT / "reports" / "hand_contact_guard_v5.json"

assert SRC.is_file(), SRC
assert V8_GLB.is_file(), V8_GLB
assert CONTACT_REPORT.is_file(), CONTACT_REPORT
assert not OUT.exists(), f"Refusing to overwrite {OUT.name}"

# Reproduce the V8 Blender-vertex -> GLB-vertex mapping used by the earlier
# hand scripts so the original 682 push-up contacts remain the authority.
raw = V8_GLB.read_bytes()
json_len = struct.unpack_from("<I", raw, 12)[0]
doc = json.loads(raw[20:20 + json_len])
bin_base = 28 + json_len
accessor = doc["accessors"][doc["meshes"][0]["primitives"][0]["indices"]]
view = doc["bufferViews"][accessor["bufferView"]]
dtype = np.dtype({5125: "<u4", 5123: "<u2"}[accessor["componentType"]])
indices = np.ndarray(
    accessor["count"],
    dtype=dtype,
    buffer=raw,
    offset=bin_base + view.get("byteOffset", 0) + accessor.get("byteOffset", 0),
).reshape(-1, 3)
protected_glb = set(json.loads(CONTACT_REPORT.read_text())["original_vertex_ids"])

bpy.ops.wm.open_mainfile(filepath=str(ROOT / "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy.blend"))
v8_mesh = bpy.data.objects["Mike_Freeman"].data
mapping = [set() for _ in v8_mesh.vertices]
for face_i, poly in enumerate(v8_mesh.polygons):
    for corner_i, loop_i in enumerate(poly.loop_indices):
        mapping[v8_mesh.loops[loop_i].vertex_index].add(int(indices[face_i, corner_i]))
protected_source_ids = {i for i, ids in enumerate(mapping) if ids & protected_glb}

bpy.ops.wm.open_mainfile(filepath=str(SRC))
body = bpy.data.objects["Mike_Freeman"]
mesh = body.data

# This script must never alter geometry.
original = np.array([tuple(v.co) for v in mesh.vertices], dtype=np.float64)

bm = bmesh.new()
bm.from_mesh(mesh)
bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
bm.normal_update()

sid = bm.verts.layers.int.get("v8_source_id")
if sid is None:
    raise RuntimeError("V13e is missing v8_source_id")
dlay = bm.verts.layers.deform.active
if dlay is None:
    raise RuntimeError("Body mesh has no deform layer")

group_names = {g.index: g.name for g in body.vertex_groups}
digit_keys = {}
for side in ("L", "R"):
    for digit in ("index", "middle", "ring", "pinky"):
        key = f"{digit.upper()}_{side}"
        digit_keys[key] = {
            gid
            for gid, name in group_names.items()
            if f"DEF-f_{digit}." in name and name.endswith("." + side)
        }

def source_id(v):
    return v[sid] - 1 if v[sid] > 0 else -1

def is_protected(v):
    s = source_id(v)
    return s >= 0 and s in protected_source_ids

def influence(v, gids):
    return sum(w for gid, w in v[dlay].items() if gid in gids)

def owner(v):
    values = {key: influence(v, gids) for key, gids in digit_keys.items()}
    key = max(values, key=values.get)
    return key, values[key]

owners = {}
for v in bm.verts:
    key, weight = owner(v)
    if weight > 0.65:
        owners[v] = key

protected = {v for v in bm.verts if is_protected(v)}
# Only digit-owned patch boundaries matter to this hand rebuild. Whole-body
# mesh boundaries would make the diagnostic group noisy and waste Work time.
boundaries = {v for v in owners if v.is_boundary}

# Keep a four-edge transition region around exact contact and existing patch
# boundaries. V15_REBUILD_CORE deliberately excludes that transition.
anchors = protected | boundaries
distance = {v: 0 for v in anchors}
front = set(anchors)
for depth in range(1, 5):
    nxt = {
        e.other_vert(v)
        for v in front
        for e in v.link_edges
        if e.other_vert(v) not in distance
    }
    for v in nxt:
        distance[v] = depth
    front = nxt

sharp = set()
threshold_cos = math.cos(math.radians(35.0))
for e in bm.edges:
    if len(e.link_faces) != 2:
        continue
    a, b = e.verts
    if a not in owners or b not in owners or owners[a] != owners[b]:
        continue
    if e.link_faces[0].normal.dot(e.link_faces[1].normal) < threshold_cos:
        sharp.update(e.verts)

rebuild_core = {
    v
    for v in owners
    if v not in protected
    and v not in boundaries
    and distance.get(v, 99) >= 4
}

def replace_group(name, verts):
    old = body.vertex_groups.get(name)
    if old is not None:
        body.vertex_groups.remove(old)
    vg = body.vertex_groups.new(name=name)
    ids = sorted(v.index for v in verts)
    if ids:
        vg.add(ids, 1.0, "REPLACE")
    return len(ids)

counts = {}
counts["V15_PROTECTED_PUSHUP"] = replace_group("V15_PROTECTED_PUSHUP", protected)
counts["V15_PATCH_BOUNDARY"] = replace_group("V15_PATCH_BOUNDARY", boundaries)
counts["V15_SHARP_FOLD_35"] = replace_group("V15_SHARP_FOLD_35", sharp)
counts["V15_REBUILD_CORE"] = replace_group("V15_REBUILD_CORE", rebuild_core)

for key in sorted(digit_keys):
    verts = {v for v, owner_key in owners.items() if owner_key == key}
    counts["V15_" + key] = replace_group("V15_" + key, verts)

bm.free()
mesh.update()

after = np.array([tuple(v.co) for v in mesh.vertices], dtype=np.float64)
max_move = float(np.linalg.norm(after - original, axis=1).max()) if len(after) else 0.0
if max_move > 1e-12:
    raise RuntimeError(f"Diagnostic prep changed geometry by {max_move * 1000:.9f} mm")

body["v15_prep_note"] = (
    "Diagnostic selections only. Geometry unchanged. "
    "Start deep finger shaft/joint rebuild from V13e; V14e is not the baseline."
)

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT))

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "source": SRC.name,
    "output": OUT.name,
    "geometry_max_move_mm": max_move * 1000.0,
    "groups": counts,
    "protected_source_ids": len(protected_source_ids),
    "instruction": "Do not move V15_PROTECTED_PUSHUP. Treat V15_PATCH_BOUNDARY and its transition ring as anchors unless explicitly rebuilding a local bridge.",
}, indent=2))

print("V15_PREP", REPORT.read_text(), flush=True)
