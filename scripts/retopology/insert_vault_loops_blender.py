"""Add edge loops across the armpit vault where the skin takes the raise - writes a NEW file (bound rig file).

STATUS: TRIAL, NOT ADOPTED (round AX3). Cuts 0-1 x1 + 1-2 x2 pass every guard (+256 vertices per side, 0 n-gons, 0
rest intersections, drivers kept), but extra rows do not lower the strain (a quad stretched x6 splits into two quads
stretched x6) and the corner-pattern quads of the 64->48 transition crumple into small shards on the front vault at
135-170 deg. The weight relaxation alone (axillary_ring_relax_blender.py, rig 06i) is the adopted fix.

Measured on 06h: the vault between the chest wall and the inner arm (80-170 mm below the shoulder joint, both walls of
the gap between arm and chest) is lined by only cap rings 0-2, on the source surface (mean 0.1-2.3 mm) but with tall
quads; at 135 deg the rungs between rings 0-1 / 1-2 stretch x7.6 / x10.5 (ring 5 and up: x2). The gaps 0-1 and 1-2
are clean closed strips of 64 quads per side (each quad has exactly two rungs), so a loop can be cut through each
without poles or n-gons:
  * the rung edges of each gap are subdivided CUTS times (bmesh subdivide_edges, quad-ring split; the 16 'fan' quads per
    side in gap 1-2 that reduce the ring from 64 to 48 have two rungs meeting at a corner and are split with the corner
    pattern INNER_VERT - three quads - not a straight cut, which gave n-gons); bone weights and shape-key layers are
    interpolated by bmesh;
  * the new vertices are labelled as cap (torso-shell / hand / leg tags cleared) and put on the source surface by a ray
    along their own normal (within SNAP_MAX), accepting only a surface facing the same way - nearest-point snapping
    jumped to the opposite wall of the narrow arm/chest gap (10 rest intersections); every shape-key layer is moved by
    the same offset, so key deltas are kept; a snapped vertex on a face whose triangles then intersect other skin is put back to
    its interpolated position (on the rung chord, < 1 cm from the surface);
  * guards: only quads in the gaps, manifold, no n-gons, rest self-intersections not increased, drivers kept.
Run on a bound file (MESHY_RIG / MESHY_BODY); the source surface is appended from the retopology checkpoint given.

usage: python3.13 insert_vault_loops_blender.py -- <bound .blend> <retopo checkpoint with source proxy> <out NEW .blend> <report .json> [cuts 0-1] [cuts 1-2]
"""
import json
import sys
from collections import deque
from pathlib import Path

import bpy
import bmesh  # noqa: E402
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
IN, SRCBLEND, OUT, REP = Path(a[0]), Path(a[1]), Path(a[2]), Path(a[3])
CUTS = {k: n for k, n in ((0, int(a[4]) if len(a) > 4 else 1), (1, int(a[5]) if len(a) > 5 else 1)) if n > 0}
if OUT.exists():
    raise FileExistsError(f"will not overwrite {OUT}")
SNAP_MAX = 0.012
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
with bpy.data.libraries.load(str(SRCBLEND), link=False) as (src, dst):
    dst.objects = ["HGPT_SOURCE_PROXY_Mesh_0"]
S = dst.objects[0]
sb = BVHTree.FromPolygons([v.co.copy() for v in S.data.vertices], [tuple(p.vertices) for p in S.data.polygons])
body = bpy.data.objects["MESHY_BODY"]; me = body.data
drivers0 = len(me.shape_keys.animation_data.drivers) if me.shape_keys and me.shape_keys.animation_data else 0
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
LR, LC = bm.verts.layers.int["t3_row"], bm.verts.layers.int["t3_col"]; L4, L5 = bm.verts.layers.int["t4_part"], bm.verts.layers.int["t5_part"]
SK = list(bm.verts.layers.shape.values())


def intersections():
    tris = bm.calc_loop_triangles(); T = [tuple(l.vert.index for l in t) for t in tris]
    bm.verts.ensure_lookup_table(); b = BVHTree.FromPolygons([v.co.copy() for v in bm.verts], T, all_triangles=True)
    return sum(1 for i, j in b.overlap(b) if not set(T[i]) & set(T[j]))


def rings(sg):
    shell = {v for v in bm.verts if v[LR] > 0 or v[LC] > 0}
    cap = {v for v in bm.verts if v not in shell and v[L4] == 0 and v[L5] == 0 and v.co.z > 0.95}
    rim = [v for v in shell if v.co.x * sg > 0.1 and any(e.other_vert(v) in cap for e in v.link_edges)]
    ring = {v: 0 for v in rim}; q = deque(rim)
    while q:
        v = q.popleft()
        for e in v.link_edges:
            w = e.other_vert(v)
            if w in cap and w not in ring and w.co.x * sg > 0.05:
                ring[w] = ring[v] + 1; q.append(w)
    return ring


def intersect_verts():
    tris = bm.calc_loop_triangles(); T = [tuple(l.vert for l in t) for t in tris]
    b = BVHTree.FromPolygons([v.co.copy() for v in bm.verts], [tuple(x.index for x in t) for t in T], all_triangles=True)
    out = set()
    for i, j in b.overlap(b):
        if not set(T[i]) & set(T[j]):
            out |= set(T[i]) | set(T[j])
    return out


SNX, SNY, SNZ = (bm.verts.layers.float.new(n) for n in ("_snx", "_sny", "_snz"))   # snap offset per vertex (for reverting;
                                                               # BMVert references do not survive the later subdivisions)
inter0 = intersections(); nv0 = len(bm.verts); rep = {"method": __doc__.split("usage")[0].strip(), "cuts": CUTS, "sides": {}}
for sd, sg in (("r", 1), ("l", -1)):
    ring = rings(sg); rungs = {k: [e for e in bm.edges if all(x in ring for x in e.verts) and sorted(ring[x] for x in e.verts) == [k, k + 1]] for k in CUTS}
    side = {"new_vertices": 0, "snap_mm_max": 0.0}
    for k in sorted(CUTS, reverse=True):                    # cut the outer gap first so ring labels of the inner stay valid
        es = rungs[k]
        faces = {f for e in es for f in e.link_faces if all(ring.get(x, -1) in (k, k + 1) for x in f.verts)}
        if not es or any(len(f.verts) != 4 or sum(1 for e in f.edges if e in es) != 2 for f in faces):
            raise RuntimeError(f"{sd}: gap {k}-{k + 1} is not a clean quad strip")
        res = bmesh.ops.subdivide_edges(bm, edges=es, cuts=CUTS[k], use_grid_fill=False, quad_corner_type="INNER_VERT")
        new = [g for g in res["geom_inner"] if isinstance(g, bmesh.types.BMVert)]
        bm.normal_update()
        for v in new:
            v[LR] = 0; v[LC] = 0; v[L4] = 0; v[L5] = 0
            n = v.normal; best = None
            for d in (n, -n):                                  # along the vertex normal only, and only onto a surface
                h = sb.ray_cast(v.co, d, SNAP_MAX)             # facing the same way (never the opposite wall of the gap)
                if h[0] is not None and h[1].dot(n) > 0.3 and (best is None or h[3] < best[3]):
                    best = h
            if best is not None:
                off = best[0] - v.co; side["snap_mm_max"] = max(side["snap_mm_max"], off.length * 1000)
                for L in SK:
                    v[L] = v[L] + off
                v.co = best[0]; v[SNX], v[SNY], v[SNZ] = off
        side["new_vertices"] += len(new)
    side["snap_mm_max"] = round(side["snap_mm_max"], 1); rep["sides"][sd] = side
bm.verts.ensure_lookup_table(); bm.verts.index_update(); reverted = 0
for _ in range(6):                                             # a snap that makes skin cross skin is undone
    iv = intersect_verts()                                     # a moved vertex can flip its quad's diagonal, so the
    bad = {w for v in iv for f in v.link_faces for w in f.verts if w[SNX] or w[SNY] or w[SNZ]}   # whole face neighbourhood
    if not bad:
        break
    for v in bad:
        off = Vector((v[SNX], v[SNY], v[SNZ])); v[SNX] = v[SNY] = v[SNZ] = 0.0; v.co = v.co - off; reverted += 1
        for L in SK:
            v[L] = v[L] - off
rep["snaps_reverted"] = reverted
for n in ("_snx", "_sny", "_snz"):                            # by name: removing one layer invalidates the others
    bm.verts.layers.float.remove(bm.verts.layers.float[n])
bm.normal_update()
ngons = sum(1 for f in bm.faces if len(f.verts) > 4); nonman = sum(1 for e in bm.edges if not e.is_manifold and not e.is_boundary)
inter1 = intersections()
rep.update(vertices_before=nv0, vertices_after=len(bm.verts), ngons=ngons, non_manifold_edges=nonman,
           rest_self_intersections_before=inter0, rest_self_intersections_after=inter1)
if ngons or nonman or inter1 > inter0:
    rep["status"] = "REJECTED by guard"; REP.write_text(json.dumps(rep, indent=1)); print("LOOPS", json.dumps({k: v for k, v in rep.items() if k != "method"})); sys.exit(1)
bm.to_mesh(me); me.update()
for v in me.vertices[nv0:]:                                    # interpolation can give a new vertex 5 influences: keep 4
    gs = sorted(((g.group, g.weight) for g in v.groups), key=lambda t: -t[1])
    if len(gs) > 4:
        tot = sum(w for _, w in gs[:4])
        for gi, _ in gs[4:]:
            body.vertex_groups[gi].remove([v.index])
        for gi, w in gs[:4]:
            body.vertex_groups[gi].add([v.index], w / tot, "REPLACE")
rep["drivers_before_after"] = [drivers0, len(me.shape_keys.animation_data.drivers) if me.shape_keys and me.shape_keys.animation_data else 0]
bpy.data.objects.remove(S, do_unlink=True)
body["VAULT_LOOPS"] = json.dumps({k: v for k, v in rep.items() if k != "method"})
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = OUT.name; REP.write_text(json.dumps(rep, indent=1)); print("LOOPS", json.dumps({k: v for k, v in rep.items() if k != "method"}))
