"""Blender-side V15 deep-hand invariant audit.

Run after the V15 Blender edit, before/after GLB export:

    blender --background --python scripts/audit_v15_hand_blender.py -- \
      HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v15a_deep_hand_rebuild.blend

This does not edit or save the candidate. It verifies that a deep digit rebuild
did not leak into protected push-up contact, non-digit body/palm/thumb/wrist
geometry, or skin data. All original V8-source vertex records must survive so
the stable-ID GLB packer and downstream guards remain valid.
"""
from __future__ import annotations

import bpy
import bmesh
import hashlib
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

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
candidate = Path(args[0]).resolve() if args else DEFAULT
prefix = "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_"
version = candidate.stem[len(prefix):] if candidate.stem.startswith(prefix) else candidate.stem
REPORT = ROOT / "reports" / f"audit_{version}_blender.json"
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

    def digit_owner(v):
        values = {
            key: sum(w for gid, w in v[dlay].items() if gid in ids)
            for key, ids in digit_group_ids.items()
        }
        key = max(values, key=values.get)
        return key if values[key] > 0.65 else None

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
                "digit_key": digit_owner(v),
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

    # Per-digit surface faceting diagnostics. These are not acceptance scores:
    # a real knuckle can have a deliberate crease. They locate where broad
    # planar segmentation remains and let V13e/V15 be compared consistently.
    thresholds = (20, 35, 50, 75, 100)
    per_digit = {
        key: {
            "owned_vertices": sum(owner_key == key for owner_key in owned.values()),
            "edges_total": 0,
            "boundary_edges": 0,
            "total_edge_length_mm": 0.0,
            "edge_lengths_mm": [],
            "dihedral_edge_count_gt_deg": {str(t): 0 for t in thresholds},
            "dihedral_edge_length_mm_gt_deg": {str(t): 0.0 for t in thresholds},
        }
        for key in digit_group_ids
    }
    for e in bm.edges:
        a, b = e.verts
        if a not in owned or b not in owned or owned[a] != owned[b]:
            continue
        key = owned[a]
        item = per_digit[key]
        length_mm = e.calc_length() * 1000.0
        item["edges_total"] += 1
        item["total_edge_length_mm"] += length_mm
        item["edge_lengths_mm"].append(length_mm)
        if e.is_boundary:
            item["boundary_edges"] += 1
        if len(e.link_faces) != 2:
            continue
        dot = max(-1.0, min(1.0, e.link_faces[0].normal.dot(e.link_faces[1].normal)))
        angle = math.degrees(math.acos(dot))
        for threshold in thresholds:
            if angle > threshold:
                item["dihedral_edge_count_gt_deg"][str(threshold)] += 1
                item["dihedral_edge_length_mm_gt_deg"][str(threshold)] += length_mm

    for item in per_digit.values():
        lengths = item.pop("edge_lengths_mm")
        total = item["total_edge_length_mm"]
        item["edge_p50_mm"] = float(np.percentile(lengths, 50)) if lengths else 0.0
        item["edge_p90_mm"] = float(np.percentile(lengths, 90)) if lengths else 0.0
        item["sharp_length_ratio_gt_35"] = (
            item["dihedral_edge_length_mm_gt_deg"]["35"] / total if total else 0.0
        )
        item["sharp_length_ratio_gt_50"] = (
            item["dihedral_edge_length_mm_gt_deg"]["50"] / total if total else 0.0
        )

    # Deterministic per-digit bind-surface fingerprint. This is used by V15f
    # visual decision markers so a reviewed ring_L surface remains approved
    # while ring_R/pinky/index/middle are edited, but becomes stale if ring_L
    # itself changes. Hash local coordinates plus same-owner edge connectivity;
    # avoid global vertex indices so unrelated appended vertices do not invalidate it.
    def qco(v):
        return tuple(round(float(x), 9) for x in v.co)

    for key, item in per_digit.items():
        verts = [v for v, owner_key in owned.items() if owner_key == key]
        coords = sorted(qco(v) for v in verts)
        edges = []
        for e in bm.edges:
            a, b = e.verts
            if owned.get(a) != key or owned.get(b) != key:
                continue
            qa, qb = qco(a), qco(b)
            edges.append((qa, qb) if qa <= qb else (qb, qa))
        payload = json.dumps(
            {"vertices": coords, "edges": sorted(edges)},
            separators=(",", ":"),
        ).encode("utf-8")
        item["surface_fingerprint_sha256"] = hashlib.sha256(payload).hexdigest()

    # Finger shape-profile diagnostics. These are deliberately advisory, not
    # acceptance gates yet. They measure whether a finger still has abrupt
    # cross-section/diameter changes even when dihedral counts improve.
    #
    # Each digit is projected along its three-bone centerline. In longitudinal
    # bins we report radial spread, transverse axis ratio and adjacent radius
    # jumps. This helps distinguish a genuinely smoother shaft from a lower
    # fold count that still looks segmented/"sausage-link".
    arm = bpy.data.objects.get("HomeGymPT_Male_Rig")
    if arm is not None:
        to_body = body.matrix_world.inverted() @ arm.matrix_world

        def chain_points(digit, side):
            bones = arm.data.bones
            names = [f"DEF-f_{digit}.{i:02d}.{side}" for i in (1, 2, 3)]
            if any(name not in bones for name in names):
                return None
            b1, b2, b3 = [bones[name] for name in names]
            return [
                to_body @ b1.head_local,
                to_body @ b1.tail_local,
                to_body @ b2.tail_local,
                to_body @ b3.tail_local,
            ]

        def chain_lengths(chain):
            lengths = [(b - a).length for a, b in zip(chain[:-1], chain[1:])]
            total = sum(lengths)
            cumulative = [0.0]
            for length in lengths:
                cumulative.append(cumulative[-1] + length)
            return lengths, cumulative, total

        def closest_arc(point, chain, lengths, cumulative):
            best = None
            for i, (a, b) in enumerate(zip(chain[:-1], chain[1:])):
                ab = b - a
                length = lengths[i]
                if length <= 1e-12:
                    continue
                t = max(0.0, min(1.0, (point - a).dot(ab) / (length * length)))
                q = a + t * ab
                d2 = (point - q).length_squared
                item = (d2, cumulative[i] + t * length)
                if best is None or item[0] < best[0]:
                    best = item
            return best[1] if best is not None else 0.0

        def chain_point_tangent(chain, lengths, cumulative, arc):
            arc = max(0.0, min(float(arc), cumulative[-1]))
            for i, (a, b) in enumerate(zip(chain[:-1], chain[1:])):
                if arc <= cumulative[i + 1] + 1e-12:
                    length = lengths[i]
                    if length <= 1e-12:
                        return a.copy(), Vector((1.0, 0.0, 0.0))
                    t = (arc - cumulative[i]) / length
                    return a.lerp(b, max(0.0, min(1.0, t))), (b - a).normalized()
            return chain[-1].copy(), (chain[-1] - chain[-2]).normalized()

        def percentile(values, q):
            return float(np.percentile(values, q)) if values else 0.0

        for key, item in per_digit.items():
            digit, side = key.rsplit("_", 1)
            chain = chain_points(digit, side)
            if chain is None:
                item["shape_profile"] = {"available": False}
                continue

            lengths, cumulative, total_length = chain_lengths(chain)
            verts = [v for v, owner_key in owned.items() if owner_key == key]
            bin_count = 14
            bins = [[] for _ in range(bin_count)]
            if total_length > 1e-12:
                for v in verts:
                    arc = closest_arc(v.co, chain, lengths, cumulative)
                    u = max(0.0, min(0.999999, arc / total_length))
                    bins[int(u * bin_count)].append(v.co.copy())

            sections = []
            for i, points in enumerate(bins):
                if len(points) < 4:
                    continue
                arc = ((i + 0.5) / bin_count) * total_length
                center, tangent = chain_point_tangent(chain, lengths, cumulative, arc)

                ref = Vector((0.0, 0.0, 1.0))
                if abs(tangent.dot(ref)) > 0.9:
                    ref = Vector((0.0, 1.0, 0.0))
                axis_u = tangent.cross(ref)
                if axis_u.length <= 1e-12:
                    axis_u = Vector((1.0, 0.0, 0.0))
                else:
                    axis_u.normalize()
                axis_v = tangent.cross(axis_u).normalized()

                transverse = []
                radii = []
                for p in points:
                    delta = p - center
                    x = float(delta.dot(axis_u))
                    y = float(delta.dot(axis_v))
                    transverse.append((x, y))
                    radii.append(math.sqrt(x * x + y * y))

                mean_radius = float(np.mean(radii)) if radii else 0.0
                std_radius = float(np.std(radii)) if radii else 0.0
                radius_cv = std_radius / mean_radius if mean_radius > 1e-12 else 0.0

                axis_ratio = 0.0
                if len(transverse) >= 4:
                    arr = np.asarray(transverse, dtype=float)
                    cov = np.cov(arr, rowvar=False)
                    eig = np.linalg.eigvalsh(cov)
                    high = max(float(eig[-1]), 0.0)
                    low = max(float(eig[0]), 0.0)
                    if high > 1e-18:
                        axis_ratio = math.sqrt(low / high)

                sections.append({
                    "bin": i,
                    "point_count": len(points),
                    "arc_fraction": (i + 0.5) / bin_count,
                    "mean_radius_mm": mean_radius * 1000.0,
                    "radius_cv": radius_cv,
                    "transverse_axis_ratio": axis_ratio,
                })

            means = [s["mean_radius_mm"] for s in sections]
            median_radius = float(np.median(means)) if means else 0.0
            jumps = [
                abs(b - a) / median_radius
                for a, b in zip(means[:-1], means[1:])
                if median_radius > 1e-12
            ]
            second = [
                abs(means[i + 1] - 2.0 * means[i] + means[i - 1]) / median_radius
                for i in range(1, len(means) - 1)
                if median_radius > 1e-12
            ]
            cvs = [s["radius_cv"] for s in sections]
            axis_ratios = [s["transverse_axis_ratio"] for s in sections]

            item["shape_profile"] = {
                "available": bool(sections),
                "section_bins_requested": bin_count,
                "section_bins_used": len(sections),
                "median_radius_mm": median_radius,
                "radius_cv_median": percentile(cvs, 50),
                "radius_cv_p90": percentile(cvs, 90),
                "transverse_axis_ratio_median": percentile(axis_ratios, 50),
                "transverse_axis_ratio_p10": percentile(axis_ratios, 10),
                "radius_profile_jump_p90_norm": percentile(jumps, 90),
                "radius_profile_jump_max_norm": max(jumps) if jumps else 0.0,
                "radius_profile_second_diff_p90_norm": percentile(second, 90),
                "sections": sections,
                "note": (
                    "Advisory bind-pose shape metric. Lower radius-profile jump/"
                    "second-difference suggests smoother diameter continuity; "
                    "axis ratio closer to 1 suggests a rounder sampled cross-section."
                ),
            }

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
        "per_digit_surface": per_digit,
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
per_digit_original_movement = {
    key: {
        "max_move_mm": 0.0,
        "moved_source_vertices": 0,
        "max_weight_delta": 0.0,
        "weight_rows_changed": 0,
    }
    for key in baseline["per_digit_surface"]
}

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
        key = a.get("digit_key")
        if key in per_digit_original_movement:
            item = per_digit_original_movement[key]
            item["max_move_mm"] = max(item["max_move_mm"], move)
            item["max_weight_delta"] = max(item["max_weight_delta"], wdelta)
            if move > 1e-6:
                item["moved_source_vertices"] += 1
            if wdelta > 1e-7:
                item["weight_rows_changed"] += 1

original_digit_weight_rows_changed = sum(
    item["weight_rows_changed"] for item in per_digit_original_movement.values()
)

# V13e itself may contain inherited hand boundaries/folds; V15 must not make
# topology health worse while rebuilding the digit surface.
checks = {
    "all_original_source_ids_present": not missing,
    "protected_source_ids_present": not missing_protected,
    "protected_positions_exact": protected_move < 1e-6,
    "protected_bone_weights_exact": protected_weight_changed == 0,
    "non_digit_source_ids_present": not missing_non_digit,
    "non_digit_positions_exact": non_digit_move < 1e-6,
    "non_digit_bone_weights_exact": non_digit_weight_changed == 0,
    "digit_original_move_within_10mm": digit_move <= 10.0 + 1e-6,
    "original_digit_bone_weights_exact": original_digit_weight_rows_changed == 0,
    "no_duplicate_source_ids": not cand["duplicate_source_ids"],
    "degenerates_not_increased": cand["degenerate_faces"] <= baseline["degenerate_faces"],
    "nonmanifold_gt2_not_increased": cand["nonmanifold_edges_gt2"] <= baseline["nonmanifold_edges_gt2"],
    "digit_boundaries_not_increased": cand["digit_boundary_edges"] <= baseline["digit_boundary_edges"],
    "new_digit_bone_weights_normalized": cand["new_digit_weight_max_error"] <= 1e-4,
}

surface_deltas = {}
for key in sorted(set(baseline["per_digit_surface"]) & set(cand["per_digit_surface"])):
    b = baseline["per_digit_surface"][key]
    d = cand["per_digit_surface"][key]
    surface_deltas[key] = {
        "sharp_length_ratio_gt_35_delta": d["sharp_length_ratio_gt_35"] - b["sharp_length_ratio_gt_35"],
        "sharp_length_ratio_gt_50_delta": d["sharp_length_ratio_gt_50"] - b["sharp_length_ratio_gt_50"],
        "fold_edges_gt_100_delta": (
            d["dihedral_edge_count_gt_deg"]["100"] - b["dihedral_edge_count_gt_deg"]["100"]
        ),
        "boundary_edge_delta": d["boundary_edges"] - b["boundary_edges"],
        "shape_profile_jump_p90_delta": (
            d.get("shape_profile", {}).get("radius_profile_jump_p90_norm", 0.0)
            - b.get("shape_profile", {}).get("radius_profile_jump_p90_norm", 0.0)
        ),
        "shape_profile_second_diff_p90_delta": (
            d.get("shape_profile", {}).get("radius_profile_second_diff_p90_norm", 0.0)
            - b.get("shape_profile", {}).get("radius_profile_second_diff_p90_norm", 0.0)
        ),
        "shape_radius_cv_p90_delta": (
            d.get("shape_profile", {}).get("radius_cv_p90", 0.0)
            - b.get("shape_profile", {}).get("radius_cv_p90", 0.0)
        ),
        "shape_axis_ratio_median_delta": (
            d.get("shape_profile", {}).get("transverse_axis_ratio_median", 0.0)
            - b.get("shape_profile", {}).get("transverse_axis_ratio_median", 0.0)
        ),
    }

shape_quality_priority = sorted(
    (
        {
            "digit": key,
            "candidate_radius_profile_jump_p90_norm": (
                cand["per_digit_surface"][key]
                .get("shape_profile", {})
                .get("radius_profile_jump_p90_norm", 0.0)
            ),
            "candidate_second_diff_p90_norm": (
                cand["per_digit_surface"][key]
                .get("shape_profile", {})
                .get("radius_profile_second_diff_p90_norm", 0.0)
            ),
            "jump_delta_vs_v13e": surface_deltas[key]["shape_profile_jump_p90_delta"],
            "second_diff_delta_vs_v13e": surface_deltas[key]["shape_profile_second_diff_p90_delta"],
        }
        for key in cand["per_digit_surface"]
    ),
    key=lambda item: (
        item["candidate_radius_profile_jump_p90_norm"],
        item["candidate_second_diff_p90_norm"],
    ),
    reverse=True,
)

faceting_priority = sorted(
    (
        {
            "digit": key,
            "candidate_sharp_ratio_gt_35": cand["per_digit_surface"][key]["sharp_length_ratio_gt_35"],
            "candidate_sharp_ratio_gt_50": cand["per_digit_surface"][key]["sharp_length_ratio_gt_50"],
            "delta_gt_35_vs_v13e": surface_deltas[key]["sharp_length_ratio_gt_35_delta"],
        }
        for key in cand["per_digit_surface"]
    ),
    key=lambda item: (
        item["candidate_sharp_ratio_gt_50"],
        item["candidate_sharp_ratio_gt_35"],
    ),
    reverse=True,
)

report = {
    "version": version,
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
    "original_digit_weight_rows_changed": original_digit_weight_rows_changed,
    "per_digit_original_movement_vs_v13e": per_digit_original_movement,
    "baseline_topology": baseline,
    "candidate_topology": cand,
    "per_digit_surface_delta_vs_v13e": surface_deltas,
    "remaining_faceting_priority": faceting_priority,
    "shape_quality_priority": shape_quality_priority,
    "checks": checks,
    "pass": all(checks.values()),
    "note": (
        "All original V8-source IDs must survive. Rebuild topology by "
        "rewiring/retriangulating and adding vertices, not by deleting source vertices."
    ),
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(report, indent=2))
print("V15_HAND_AUDIT", json.dumps(report, indent=2), flush=True)
if not report["pass"]:
    raise SystemExit(1)
