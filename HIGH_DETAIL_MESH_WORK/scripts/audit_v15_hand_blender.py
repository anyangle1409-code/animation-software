"""Blender-side V15 deep-hand invariant audit.

Run after the V15 Blender edit, before/after GLB export:

    blender --background --python scripts/audit_v15_hand_blender.py -- \
      HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v15a_deep_hand_rebuild.blend

This does not edit or save the candidate. It verifies that a deep digit rebuild
did not leak into protected push-up contact, non-digit body/palm/thumb/wrist
geometry, or skin data. Digit-interior source vertices may be removed/replaced.
"""
from __future__ import annotations

import bpy
import bmesh
import json
import math
import struct
import sys
from pathlib import Path
from collections import defaultdict

import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v13e_fingertip_retopology.blend"
V8_GLB = ROOT / "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy.glb"
CONTACT = ROOT / "reports" / "hand_contact_guard_v5.json"
DEFAULT = ROOT / "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v15a_deep_hand_rebuild.blend"
REPORT = ROOT / "reports" / "audit_v15a_deep_hand_rebuild_blender.json"

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
candidate = Path(args[0]).resolve() if args else DEFAULT
if not candidate.is_file():
    raise SystemExit(f"Missing V15 Blend: {candidate}")
for p in (BASE, V8_GLB, CONTACT):
    if not p.is_file():
        raise SystemExit(f"Missing required baseline: {p}")

# Recover the authoritative protected V8 Blender source IDs.
raw = V8_GLB.read_bytes()
json_len = struct.unpack_from("<I", raw, 12)[0]
doc = json.loads(raw[20:20 + json_len])
base = 28 + json_len
acc = doc["accessors"][doc["meshes"][0]["primitives"][0]["indices"]]
view = doc["bufferViews"][acc["bufferView"]]
dtype = np.dtype({5125: "<u4", 5123: "<u2"}[acc["componentType"]])
indices = np.ndarray(
    acc["count"], dtype=dtype, buffer=raw,
    offset=base + view.get("byteOffset", 0) + acc.get("byteOffset", 0),
).reshape(-1, 3)
protected_glb = set(json.loads(CONTACT.read_text())["original_vertex_ids"])

bpy.ops.wm.open_mainfile(filepath=str(ROOT / "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy.blend"))
v8 = bpy.data.objects["Mike_Freeman"].data
mapping = [set() for _ in v8.vertices]
for face_i, poly in enumerate(v8.polygons):
    for corner_i, loop_i in enumerate(poly.loop_indices):
        mapping[v8.loops[loop_i].vertex_index].add(int(indices[face_i, corner_i]))
protected_source_ids = {i for i, ids in enumerate(mapping) if ids & protected_glb}

def snapshot(path: Path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    body = bpy.data.objects["Mike_Freeman"]
    mesh = body.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bm.normal_update()

    sid = bm.verts.layers.int.get("v8_source_id")
    dlay = bm.verts.layers.deform.active
    if sid is None or dlay is None:
        raise RuntimeError(f"{path.name}: missing v8_source_id or deform layer")

    names = {g.index: g.name for g in body.vertex_groups}
    bone_names = {g.index: g.name for g in body.vertex_groups if g.name.startswith("DEF-")}
    digit_group_ids = {
        f"{digit}_{side}": {
            gid for gid, name in names.items()
            if f"DEF-f_{digit}." in name and name.endswith("." + side)
        }
        for side in ("L", "R")
        for digit in ("index", "middle", "ring", "pinky")
    }
    digit_ids = set().union(*digit_group_ids.values())

    def bone_row(v):
        row = {}
        for gid, w in v[dlay].items():
            name = bone_names.get(gid)
            if name is not None and w:
                row[name] = float(w)
        return row

    def digit_influence(v):
        return float(sum(w for gid, w in v[dlay].items() if gid in digit_ids))

    by_source = {}
    duplicates = []
    for v in bm.verts:
        source = int(v[sid]) - 1 if v[sid] > 0 else -1
        if source >= 0:
            if source in by_source:
                duplicates.append(source)
            by_source[source] = {
                "co": tuple(float(x) for x in v.co),
                "weights": bone_row(v),
                "digit": digit_influence(v),
            }

    # Topology checks.
    degenerate = sum(1 for f in bm.faces if f.calc_area() < 1e-12)
    nonmanifold_gt2 = sum(1 for e in bm.edges if len(e.link_faces) > 2)

    # Finger-owned boundary/fold counts.
    owned = {}
    for v in bm.verts:
        values = {
            key: sum(w for gid, w in v[dlay].items() if gid in ids)
            for key, ids in digit_group_ids.items()
        }
        key = max(values, key=values.get)
        if values[key] > 0.65:
            owned[v] = key

    digit_boundary_edges = sum(
        1 for e in bm.edges
        if e.is_boundary and any(v in owned for v in e.verts)
    )
    fold_cos = math.cos(math.radians(100.0))
    digit_folds_100 = sum(
        1 for e in bm.edges
        if len(e.link_faces) == 2
        and all(v in owned for v in e.verts)
        and e.link_faces[0].normal.dot(e.link_faces[1].normal) < fold_cos
    )

    # Bone-weight normalization only; diagnostic selection groups are ignored.
    new_weight_errors = []
    for v in bm.verts:
        source = int(v[sid]) - 1 if v[sid] > 0 else -1
        if source >= 0 or v not in owned:
            continue
        total = sum(w for gid, w in v[dlay].items() if gid in bone_names)
        new_weight_errors.append(abs(float(total) - 1.0))

    # Bilateral bind symmetry of digit-owned vertices, measured as nearest
    # mirrored surface point. Report rather than assuming perfect source symmetry.
    left = [v.co.copy() for v in owned if v.co.x > 0]
    right = [v.co.copy() for v in owned if v.co.x < 0]
    symmetry = []
    if left and right:
        tree = KDTree(len(right))
        for i, p in enumerate(right):
            tree.insert(Vector((-p.x, p.y, p.z)), i)
        tree.balance()
        for p in left:
            _, _, dist = tree.find(p)
            symmetry.append(float(dist) * 1000.0)

    result = {
        "vertices": len(bm.verts),
        "faces": len(bm.faces),
        "source_vertices": by_source,
        "duplicate_source_ids": sorted(set(duplicates)),
        "degenerate_faces": degenerate,
        "nonmanifold_edges_gt2": nonmanifold_gt2,
        "digit_boundary_edges": digit_boundary_edges,
        "digit_folds_over_100deg": digit_folds_100,
        "new_digit_weight_max_error": max(new_weight_errors, default=0.0),
        "symmetry_max_mm": max(symmetry, default=0.0),
        "symmetry_p95_mm": float(np.percentile(symmetry, 95)) if symmetry else 0.0,
    }
    bm.free()
    return result

baseline = snapshot(BASE)
cand = snapshot(candidate)

bmap = baseline.pop("source_vertices")
cmap = cand.pop("source_vertices")

missing = sorted(set(bmap) - set(cmap))
missing_protected = [sid for sid in missing if sid in protected_source_ids]
missing_non_digit = [sid for sid in missing if bmap[sid]["digit"] <= 0.65]

protected_move = 0.0
protected_weight_changed = 0
non_digit_move = 0.0
non_digit_weight_changed = 0
digit_move = 0.0

def row_delta(a, b):
    keys = set(a) | set(b)
    return max((abs(a.get(k, 0.0) - b.get(k, 0.0)) for k in keys), default=0.0)

for sid in sorted(set(bmap) & set(cmap)):
    a, b = bmap[sid], cmap[sid]
    move = math.dist(a["co"], b["co"]) * 1000.0
    wdelta = row_delta(a["weights"], b["weights"])
    if sid in protected_source_ids:
        protected_move = max(protected_move, move)
        if wdelta > 1e-7:
            protected_weight_changed += 1
    if a["digit"] <= 0.65:
        non_digit_move = max(non_digit_move, move)
        if wdelta > 1e-7:
            non_digit_weight_changed += 1
    else:
        digit_move = max(digit_move, move)

# V13e itself may contain inherited hand boundaries/folds; V15 must not make
# topology health worse while rebuilding the digit surface.
checks = {
    "protected_source_ids_present": not missing_protected,
    "protected_positions_exact": protected_move < 1e-6,
    "protected_bone_weights_exact": protected_weight_changed == 0,
    "non_digit_source_ids_present": not missing_non_digit,
    "non_digit_positions_exact": non_digit_move < 1e-6,
    "non_digit_bone_weights_exact": non_digit_weight_changed == 0,
    "digit_original_move_within_10mm": digit_move <= 10.0 + 1e-6,
    "no_duplicate_source_ids": not cand["duplicate_source_ids"],
    "degenerates_not_increased": cand["degenerate_faces"] <= baseline["degenerate_faces"],
    "nonmanifold_gt2_not_increased": cand["nonmanifold_edges_gt2"] <= baseline["nonmanifold_edges_gt2"],
    "digit_boundaries_not_increased": cand["digit_boundary_edges"] <= baseline["digit_boundary_edges"],
    "new_digit_bone_weights_normalized": cand["new_digit_weight_max_error"] <= 1e-4,
}

report = {
    "baseline": BASE.name,
    "candidate": candidate.name,
    "protected_source_id_count": len(protected_source_ids),
    "missing_source_ids_total": len(missing),
    "missing_protected_source_ids": missing_protected,
    "missing_non_digit_source_ids": missing_non_digit[:50],
    "protected_max_move_mm": protected_move,
    "protected_weight_rows_changed": protected_weight_changed,
    "non_digit_max_move_mm": non_digit_move,
    "non_digit_weight_rows_changed": non_digit_weight_changed,
    "digit_original_max_move_mm": digit_move,
    "baseline_topology": baseline,
    "candidate_topology": cand,
    "checks": checks,
    "pass": all(checks.values()),
    "note": (
        "Digit-interior source IDs may be intentionally removed/replaced. "
        "Protected and non-digit source IDs may not."
    ),
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(report, indent=2))
print("V15_HAND_AUDIT", json.dumps(report, indent=2), flush=True)
if not report["pass"]:
    raise SystemExit(1)
