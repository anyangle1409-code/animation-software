"""Re-lay the arm/torso seam loops onto the anatomical axillary fold contour - writes a NEW file (geometry only).

STATUS: DIAGNOSTIC ONLY (round AX3). On 06g it reports 'no ring reaches the contour': the trunk-side cap rings run from
the torso rim up the chest wall of the narrow arm/chest gap to the vault top and then DOWN the inner arm (mean phi below
the contour per ring, right side: 51, 45, 37, 52, 64, 74, 72 mm), so no loop can be slid onto the contour without
leaving the source surface. The source's own dome is 78-98 mm below the joint and rings 1-2 already reach 81-90 mm
there (vault_dist measurement), so the vault is not misplaced: it is covered by too few rows with too steep a weight
step - fixed by axillary_ring_relax_blender.py (weights) instead.

The Task-4 shoulder cap starts on the chest wall up to 18 cm below the shoulder joint, so its loops cross the axillary
fold contour (anterior fold 110 mm, apex 90 mm, posterior fold 130 mm below the joint - the contour used by
axillary_fold_weights_blender.py) diagonally; the weight transition then cuts across quads and shows as a sharp crease
on the inner arm at 135 deg. Here the cap loops on the trunk side are slid along the surface so ONE loop lies on the
contour:
  * cap rings are found by breadth-first search from the torso/cap seam (ring 0 = the torso's socket rim); every cap
    vertex keeps the seam vertex it descends from (its meridian root);
  * phi = height below the contour (> 0 below it). R_STAR = the first ring whose trunk-side vertices lie on average at
    or above the contour;
  * on trunk-side meridians whose root lies below the contour, rings 1..R_STAR are moved vertically to
    phi = phi_root * (1 - k / R_STAR) (even spacing from the seam up to the contour, ring R_STAR on it), then put back
    on the source surface (nearest point within SNAP_MAX). Rings above R_STAR, the arm and the deltoid are not moved;
  * guards: rings must stay in order along each meridian, no self-intersection, no new fold defect, no vertex moved
    more than MAX_MOVE; vertices failing a guard keep their position.
Run on a bound file (MESHY_BODY); the source surface is appended from the retopology checkpoint given.

usage: python3.13 relay_axillary_loops.py -- <bound .blend> <retopo checkpoint with the source proxy> <out NEW .blend> <report .json>
"""
import json
import sys
from collections import deque
from pathlib import Path

import bpy
import bmesh  # noqa: E402
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
IN, SRCBLEND, OUT, REP = Path(a[0]), Path(a[1]), Path(a[2]), Path(a[3])
if OUT.exists():
    raise FileExistsError(f"will not overwrite {OUT}")
FRONT_Z, APEX_Z, BACK_Z, FRONT_Y, BACK_Y = 0.110, 0.090, 0.130, 0.045, 0.045
SNAP_MAX, MAX_MOVE = 0.012, 0.06
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
with bpy.data.libraries.load(str(SRCBLEND), link=False) as (src, dst):
    dst.objects = ["HGPT_SOURCE_PROXY_Mesh_0"]
S = dst.objects[0]
sb = BVHTree.FromPolygons([v.co.copy() for v in S.data.vertices], [tuple(p.vertices) for p in S.data.polygons])
rig = bpy.data.objects["MESHY_RIG"]; body = bpy.data.objects["MESHY_BODY"]; me = body.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
LR, LC = bm.verts.layers.int["t3_row"], bm.verts.layers.int["t3_col"]; L4, L5 = bm.verts.layers.int["t4_part"], bm.verts.layers.int["t5_part"]
shell = [(v[LR] > 0 or v[LC] > 0) for v in bm.verts]
cap = [(not shell[v.index]) and v[L4] == 0 and v[L5] == 0 and v.co.z > 0.95 for v in bm.verts]
orig = [v.co.copy() for v in bm.verts]


def smooth01(t):
    return float(np.clip(t, 0, 1) ** 2 * (3 - 2 * np.clip(t, 0, 1)))


def fold_defects(vs):
    bm.normal_update(); n = 0
    for e in {e for v in vs for e in v.link_edges}:
        if len(e.link_faces) != 2:
            continue
        f0, f1 = e.link_faces; c = np.degrees(f0.normal.angle(f1.normal, 0.0))
        if c < 50:
            continue
        s = np.degrees(sb.find_nearest(f0.calc_center_median())[1].angle(sb.find_nearest(f1.calc_center_median())[1], 0.0))
        n += int(c - s > 50)
    return n


def intersections():
    tris = bm.calc_loop_triangles(); T = [tuple(l.vert.index for l in t) for t in tris]
    b = BVHTree.FromPolygons([v.co.copy() for v in bm.verts], T, all_triangles=True)
    return sum(1 for i, j in b.overlap(b) if not set(T[i]) & set(T[j]))


rep = {"method": __doc__.split("usage")[0].strip(), "sides": {}}
inter0 = intersections()
for sd, sg in (("r", 1), ("l", -1)):
    gh = rig.matrix_world @ rig.data.bones[f"upperarm_{sd}"].head_local

    def phi(p):
        dy = p.y - gh.y; tf = smooth01(-dy / FRONT_Y); tb = smooth01(dy / BACK_Y)
        return (gh.z - p.z) - (APEX_Z + (FRONT_Z - APEX_Z) * tf + (BACK_Z - APEX_Z) * tb)
    rim = [v for v in bm.verts if shell[v.index] and v.co.x * sg > 0.1 and any(cap[e.other_vert(v).index] for e in v.link_edges)]
    ring = {v: 0 for v in rim}; root = {v: v for v in rim}; q = deque(rim)
    while q:
        v = q.popleft()
        for e in v.link_edges:
            w = e.other_vert(v)
            if cap[w.index] and w not in ring and w.co.x * sg > 0.05:
                ring[w] = ring[v] + 1; root[w] = root[v]; q.append(w)
    trunk_side = lambda v: (gh.x - v.co.x) * sg > 0.0
    stats = {}
    for v, k in ring.items():
        if trunk_side(v) and phi(root[v].co) > 0.01:
            stats.setdefault(k, []).append(phi(v.co))
    means = {k: float(np.mean(x)) for k, x in sorted(stats.items())}
    R_STAR = next((k for k, m in means.items() if k > 0 and m <= 0.0), None)
    if R_STAR is None:
        rep["sides"][sd] = {"ring_mean_phi_mm": {k: round(m * 1000, 1) for k, m in means.items()}, "status": "no ring reaches the contour"}; continue
    moved = []; snap = {}
    for v, k in ring.items():
        if 1 <= k <= R_STAR and trunk_side(v):
            p0 = phi(root[v].co)
            if p0 <= 0.01:
                continue
            target = p0 * (1 - k / R_STAR); dz = phi(v.co) - target           # phi larger = lower: move up by dz
            if abs(dz) > MAX_MOVE:
                continue
            p = v.co + Vector((0, 0, dz)); h = sb.find_nearest(p)
            if h[0] is not None and (h[0] - p).length < SNAP_MAX:
                p = h[0]
            snap[v] = v.co.copy(); v.co = p; moved.append(v)
    # guards: order along meridians (phi must decrease with ring index on the moved chains)
    bad = [v for v in moved if any(ring.get(e.other_vert(v), -9) == ring[v] - 1 and root.get(e.other_vert(v)) is root[v]
                                   and phi(e.other_vert(v).co) < phi(v.co) - 1e-4 for e in v.link_edges)]
    for v in bad:
        v.co = snap[v]
    rep["sides"][sd] = {"ring_mean_phi_mm_before": {k: round(m * 1000, 1) for k, m in means.items()}, "r_star": R_STAR,
                        "vertices_moved": len(moved) - len(bad), "order_guard_restored": len(bad),
                        "max_move_mm": round(max(((v.co - orig[v.index]).length for v in moved), default=0) * 1000, 1)}
    after = {}
    for v, k in ring.items():
        if trunk_side(v) and phi(root[v].co) > 0.01:
            after.setdefault(k, []).append(phi(v.co))
    rep["sides"][sd]["ring_mean_phi_mm_after"] = {k: round(float(np.mean(x)) * 1000, 1) for k, x in sorted(after.items())}
    rep["sides"][sd]["ring_r_star_phi_spread_mm"] = round(float(np.ptp(after[R_STAR])) * 1000, 1)
inter1 = intersections(); fd = fold_defects([v for v in bm.verts if abs(v.co.x) > 0.13 and v.co.z > 1.2])
rep.update(self_intersections_before=inter0, self_intersections_after=inter1, shoulder_fold_defects_after=fd)
if inter1 > inter0:
    rep["status"] = "REJECTED: new self-intersections"
bm.to_mesh(me); me.update()
bpy.data.objects.remove(S, do_unlink=True)
body["AXILLARY_LOOP_RELAY"] = json.dumps({k: v for k, v in rep.items() if k != "method"})
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = OUT.name; REP.write_text(json.dumps(rep, indent=1)); print("RELAY", json.dumps({k: v for k, v in rep.items() if k != "method"}))
