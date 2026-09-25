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
from mathutils import Vector

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

def closest_chain(p, chain):
    best = None
    travelled = 0.0
    for a, b in zip(chain[:-1], chain[1:]):
        ab = b - a
        length = ab.length
        if length <= 1e-12:
            continue
        t = max(0.0, min(1.0, (p - a).dot(ab) / (length * length)))
        q = a + t * ab
        item = ((p - q).length, q, travelled + t * length)
        if best is None or item[0] < best[0]:
            best = item
        travelled += length
    return best

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

# Per-digit Work selections and non-exported guide markers. These turn the
# Blender task into an ordered local rebuild instead of a search exercise.
arm = bpy.data.objects["HomeGymPT_Male_Rig"]
bones = arm.data.bones
guide_collection = bpy.data.collections.get("V15_GUIDES")
if guide_collection is not None:
    for ob in list(guide_collection.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.collections.remove(guide_collection)
guide_collection = bpy.data.collections.new("V15_GUIDES")
bpy.context.scene.collection.children.link(guide_collection)

def add_guide(name, co, size=0.005):
    ob = bpy.data.objects.new(name, None)
    ob.empty_display_type = "SPHERE"
    ob.empty_display_size = size
    ob.location = co
    ob.hide_render = True
    ob.show_in_front = True
    guide_collection.objects.link(ob)
    return ob

digit_report = {}
for key in sorted(digit_keys):
    digit, side = key.lower().rsplit("_", 1)
    side = side.upper()
    prefix = f"DEF-f_{digit}."
    chain_bones = [bones[prefix + f"{i:02d}." + side] for i in (1, 2, 3)]
    chain = [chain_bones[0].head_local.copy()] + [b.tail_local.copy() for b in chain_bones]
    segment_lengths = [(b - a).length for a, b in zip(chain[:-1], chain[1:])]
    pip_arc = segment_lengths[0]
    dip_arc = segment_lengths[0] + segment_lengths[1]
    bone_end_arc = sum(segment_lengths)

    verts = {v for v, owner_key in owners.items() if owner_key == key}
    core = verts & rebuild_core
    anchor = {v for v in verts if distance.get(v, 99) < 4}
    sharp_here = verts & sharp

    projected = []
    for v in verts:
        item = closest_chain(v.co, chain)
        if item is not None:
            projected.append((v, item[2], item[1]))
    effective_end = max((arc for _, arc, _ in projected), default=0.0)
    near_end = [v.co.copy() for v, arc, _ in projected if effective_end - arc <= 0.0015]
    surface_end = sum(near_end, Vector()) / len(near_end) if near_end else chain[-1].copy()

    # 7 mm longitudinal zones around PIP/DIP, restricted to the safe core.
    pip_zone = {v for v, arc, _ in projected if v in core and abs(arc - pip_arc) <= 0.007}
    dip_zone = {v for v, arc, _ in projected if v in core and abs(arc - dip_arc) <= 0.007}
    distal_zone = {v for v, arc, _ in projected if v in core and arc >= effective_end - 0.018}

    counts["V15_" + key] = replace_group("V15_" + key, verts)
    counts["V15_" + key + "_CORE"] = replace_group("V15_" + key + "_CORE", core)
    counts["V15_" + key + "_ANCHOR"] = replace_group("V15_" + key + "_ANCHOR", anchor)
    counts["V15_" + key + "_SHARP"] = replace_group("V15_" + key + "_SHARP", sharp_here)
    counts["V15_" + key + "_PIP_ZONE"] = replace_group("V15_" + key + "_PIP_ZONE", pip_zone)
    counts["V15_" + key + "_DIP_ZONE"] = replace_group("V15_" + key + "_DIP_ZONE", dip_zone)
    counts["V15_" + key + "_DISTAL_ZONE"] = replace_group("V15_" + key + "_DISTAL_ZONE", distal_zone)

    pretty = key
    add_guide(f"V15_GUIDE_{pretty}_ROOT", chain[0])
    add_guide(f"V15_GUIDE_{pretty}_PIP", chain[1])
    add_guide(f"V15_GUIDE_{pretty}_DIP", chain[2])
    add_guide(f"V15_GUIDE_{pretty}_BONE_TAIL", chain[3], 0.004)
    add_guide(f"V15_GUIDE_{pretty}_SURFACE_END", surface_end, 0.006)

    edge_lengths = [
        e.calc_length() * 1000.0
        for e in bm.edges
        if e.verts[0] in verts and e.verts[1] in verts
    ]
    digit_report[key] = {
        "owned_vertices": len(verts),
        "source_vertices": sum(source_id(v) >= 0 for v in verts),
        "added_vertices": sum(source_id(v) < 0 for v in verts),
        "safe_core_vertices": len(core),
        "anchor_transition_vertices": len(anchor),
        "protected_vertices": sum(v in protected for v in verts),
        "boundary_vertices": sum(v in boundaries for v in verts),
        "sharp_vertices_35deg": len(sharp_here),
        "pip_zone_vertices": len(pip_zone),
        "dip_zone_vertices": len(dip_zone),
        "distal_zone_vertices": len(distal_zone),
        "surface_end_arc_mm": effective_end * 1000.0,
        "bone_tail_arc_mm": bone_end_arc * 1000.0,
        "bone_tail_overshoot_mm": max(0.0, bone_end_arc - effective_end) * 1000.0,
        "edge_p50_mm": float(np.percentile(edge_lengths, 50)) if edge_lengths else 0.0,
        "edge_p90_mm": float(np.percentile(edge_lengths, 90)) if edge_lengths else 0.0,
    }

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
    "digit_diagnostics": digit_report,
    "guide_collection": "V15_GUIDES",
    "guide_meaning": {
        "ROOT": "first finger bone head / root reference",
        "PIP": "first finger bone tail",
        "DIP": "second finger bone tail",
        "BONE_TAIL": "frozen third finger bone tail; may overshoot visible surface",
        "SURFACE_END": "actual V13e visible distal surface centre",
    },
    "instruction": (
        "Do not move V15_PROTECTED_PUSHUP. Treat per-digit *_ANCHOR groups as "
        "fixed transitions. Work mainly inside *_CORE, using *_PIP_ZONE, "
        "*_DIP_ZONE, *_DISTAL_ZONE and *_SHARP to locate the inherited faceting. "
        "Do not delete original vertices carrying v8_source_id."
    ),
}, indent=2))

print("V15_PREP", REPORT.read_text(), flush=True)
