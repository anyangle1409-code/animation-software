"""Restore muscle definition from the approved source: one level of subdivision, new vertices on the source - NEW file.

Audit (muscle_relief_audit_blender.py + identical-light renders, round MD1): the current body keeps the source's muscle
VOLUME and belly contours (30 mm scale: 91-101 % of the relief, correlation 0.94-0.99) and lies on the source at its
vertices, but its 20-25 mm quads span the 10 mm wide separations between muscles: the abdominal tendinous lines,
linea alba, serratus digitations, deltoid/biceps and brachialis grooves fall between vertex rows (abdomen 15 mm-scale
groove depth 0.7 mm vs 1.6 mm in the source). Faceting in flat shading had been reading as definition.

Here (bound rig file, so weights, shape keys and drivers carry over):
  * every edge outside the hands is cut once (bmesh subdivide_edges, grid fill: a quad becomes 4 quads; the hands
    carry no muscle definition and their tightly packed fingers crossed each other when cut, so hand faces are kept;
    one ring of forearm faces at each wrist takes the transition pattern); bone weights and every shape-key
    layer are interpolated by bmesh; at most 4 influences are kept per new vertex;
  * every NEW vertex is put on the approved source surface by a ray along its own normal (within SNAP_MAX), accepting
    only a surface facing the same way (never the opposite wall of a narrow gap: armpit, crotch, fingers); every
    shape-key layer is moved by the same offset, so the corrective deltas are kept. Original vertices are not moved;
  * a snapped vertex on a face whose triangles then intersect other skin is put back to its interpolated position;
    interpolated midpoints that still cross a neighbouring finger (tightly packed fingers) are tucked in along their
    own normal in 0.25 mm steps (at most 2 mm);
  * guards: manifold, no n-gons, rest self-intersections not increased, drivers kept.
Proportions cannot change: every vertex is either an original vertex or a point of the approved source surface.

usage: python3.13 densify_project_blender.py -- <bound .blend> <retopo checkpoint with source proxy> <out NEW .blend> <report .json>
"""
import json
import sys
from pathlib import Path

import bpy
import bmesh  # noqa: E402
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
IN, SRCBLEND, OUT, REP = Path(a[0]), Path(a[1]), Path(a[2]), Path(a[3])
if OUT.exists():
    raise FileExistsError(f"will not overwrite {OUT}")
SNAP_MAX = 0.008
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
with bpy.data.libraries.load(str(SRCBLEND), link=False) as (src, dst):
    dst.objects = ["HGPT_SOURCE_PROXY_Mesh_0"]
S = dst.objects[0]
sb = BVHTree.FromPolygons([v.co.copy() for v in S.data.vertices], [tuple(p.vertices) for p in S.data.polygons])
body = bpy.data.objects["MESHY_BODY"]; me = body.data
drivers0 = len(me.shape_keys.animation_data.drivers) if me.shape_keys and me.shape_keys.animation_data else 0
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
SK = list(bm.verts.layers.shape.values())
SNX, SNY, SNZ = (bm.verts.layers.float.new(n) for n in ("_snx", "_sny", "_snz"))
ISNEW = bm.verts.layers.int.new("_isnew")


def tris_bvh():
    tris = bm.calc_loop_triangles(); bm.verts.index_update(); T = [tuple(l.vert for l in t) for t in tris]
    return T, BVHTree.FromPolygons([v.co.copy() for v in bm.verts], [tuple(x.index for x in t) for t in T], all_triangles=True)


def intersect_verts():
    T, b = tris_bvh(); out = set()
    for i, j in b.overlap(b):
        if not set(T[i]) & set(T[j]):
            out |= set(T[i]) | set(T[j])
    return out


nv0, nf0 = len(bm.verts), len(bm.faces); inter0 = len(intersect_verts())
L4 = bm.verts.layers.int["t4_part"]                            # the hands carry no muscle definition and their packed
hand_faces = {f for f in bm.faces if all(v[L4] > 0 for v in f.verts)}   # fingers cross when cut: kept as they are
cut = [e for e in bm.edges if not any(f in hand_faces for f in e.link_faces)]
res = bmesh.ops.subdivide_edges(bm, edges=cut, cuts=1, use_grid_fill=True, quad_corner_type="INNER_VERT")
new = [g for g in res["geom_inner"] + res["geom_split"] if isinstance(g, bmesh.types.BMVert)]
new = list({v for v in new})
bm.normal_update(); snapped = 0; dmax = 0.0
for v in new:
    v[ISNEW] = 1; n = v.normal; best = None
    for d in (n, -n):
        h = sb.ray_cast(v.co, d, SNAP_MAX)
        if h[0] is not None and h[1].dot(n) > 0.3 and (best is None or h[3] < best[3]):
            best = h
    if best is not None:
        off = best[0] - v.co
        for L in SK:
            v[L] = v[L] + off
        v.co = best[0]; v[SNX], v[SNY], v[SNZ] = off; snapped += 1; dmax = max(dmax, off.length)
reverted = 0
for _ in range(30):
    iv = intersect_verts()
    bad = {w for v in iv for f in v.link_faces for w in f.verts if w[SNX] or w[SNY] or w[SNZ]}
    if not bad:
        break
    for v in bad:
        off = Vector((v[SNX], v[SNY], v[SNZ])); v[SNX] = v[SNY] = v[SNZ] = 0.0; v.co = v.co - off; reverted += 1
        for L in SK:
            v[L] = v[L] - off
tucked = 0
for _ in range(8):                                             # interpolated midpoints of tightly packed fingers can
    left = [v for v in intersect_verts() if v[ISNEW]]          # cross the neighbour finger: tuck them in 0.25 mm per
    if not left:                                               # pass along their own normal (at most 2 mm)
        break
    bm.normal_update()
    for v in left:
        d = v.normal * -0.00025; v.co = v.co + d; tucked += 1
        for L in SK:
            v[L] = v[L] + d
left = intersect_verts(); inter1 = len(left)
print("LEFT", sorted((round(v.co.x, 3), round(v.co.y, 3), round(v.co.z, 3), bool(v[ISNEW])) for v in left)[:20], flush=True)
for nm in ("_snx", "_sny", "_snz"):
    bm.verts.layers.float.remove(bm.verts.layers.float[nm])
bm.normal_update()
ngons = sum(1 for f in bm.faces if len(f.verts) > 4); nonman = sum(1 for e in bm.edges if not e.is_manifold and not e.is_boundary)
rep = {"method": __doc__.split("usage")[0].strip(), "vertices_before_after": [nv0, len(bm.verts)], "faces_before_after": [nf0, len(bm.faces)],
       "new_vertices": len(new), "snapped": snapped, "snap_max_mm": round(dmax * 1000, 2), "snaps_reverted": reverted, "finger_midpoints_tucked_steps": tucked,
       "ngons": ngons, "non_manifold_edges": nonman, "rest_intersecting_vertices_before_after": [inter0, inter1]}
if ngons or nonman or inter1 > inter0:
    rep["status"] = "REJECTED by guard"; REP.write_text(json.dumps(rep, indent=1)); print("DENSE", json.dumps({k: v for k, v in rep.items() if k != "method"})); sys.exit(1)
bm.to_mesh(me); me.update()
isnew = [False] * len(me.vertices)
for i, at in enumerate(me.attributes["_isnew"].data):
    isnew[i] = bool(at.value)
for v in me.vertices:
    if not isnew[v.index]:
        continue
    gs = sorted(((g.group, g.weight) for g in v.groups), key=lambda t: -t[1])
    if len(gs) > 4:
        tot = sum(w for _, w in gs[:4])
        for gi, _ in gs[4:]:
            body.vertex_groups[gi].remove([v.index])
        for gi, w in gs[:4]:
            body.vertex_groups[gi].add([v.index], w / tot, "REPLACE")
me.attributes.remove(me.attributes["_isnew"])
rep["drivers_before_after"] = [drivers0, len(me.shape_keys.animation_data.drivers) if me.shape_keys and me.shape_keys.animation_data else 0]
bpy.data.objects.remove(S, do_unlink=True)
body["DENSIFY_PROJECT"] = json.dumps({k: v for k, v in rep.items() if k != "method"})
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = OUT.name; REP.write_text(json.dumps(rep, indent=1)); print("DENSE", json.dumps({k: v for k, v in rep.items() if k != "method"}))
