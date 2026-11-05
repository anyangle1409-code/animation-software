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
  * symmetry guard: where a new vertex's snap differs from its mirror twin's by more than 2.5 mm, both take the
    smaller snap (a one-sided feature is a source defect, e.g. the pit at the right acromioclavicular region that
    folded when the clavicle lifted in 07a; muscle definition is bilateral);
  * a snapped vertex on a face whose triangles then intersect other skin is put back to its interpolated position;
    interpolated midpoints that still cross a neighbouring finger (tightly packed fingers) are tucked in along their
    own normal in 0.25 mm steps (at most 2 mm);
  * posed fold guard: posed through the standard arm poses and the sweep posture, intersecting faces within 4 edges
    of each other are local folds of a source detail the skinning cannot carry (07a: a 1 cm crease in front of the
    right clavicle at 55-105 deg); snapped new vertices there return to the interpolated position;
  * guards: manifold, no n-gons, rest self-intersections not increased, drivers kept.
Proportions cannot change: every vertex is either an original vertex or a point of the approved source surface.

With a 5th argument "face" only the face (front of the head above the jaw line) is subdivided - a second level there
for the eyes, lids, lips and nose; the edges on its border are not cut, so the border faces take the transition pattern.

usage: python3.13 densify_project_blender.py -- <bound .blend> <retopo checkpoint with source proxy> <out NEW .blend> <report .json> [face]
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
REGION = a[4] if len(a) > 4 else "body"
if REGION == "face":                                           # second level on the face only (eyes, lids, lips, nose):
    def in_face(v):                                            # front of the head, above the jaw line
        return v.co.z > 1.615 and v.co.y < -0.035 and abs(v.co.x) < 0.085
    face_faces = {f for f in bm.faces if all(in_face(v) for v in f.verts)}
    cut = [e for e in bm.edges if e.link_faces and all(f in face_faces for f in e.link_faces)]
else:
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
# symmetry guard: muscle definition is bilateral; a feature on one side only (e.g. the pit in the source at the right
# acromioclavicular region, which folded when the clavicle lifted) is a source defect, not anatomy. Where a new vertex's
# snap differs from its mirror twin's (mirrored offset) by more than ASYM, both take the smaller of the two snaps.
from mathutils.kdtree import KDTree  # noqa: E402
ASYM = 0.0025; kd = KDTree(len(new))
for k, v in enumerate(new):
    kd.insert(v.co - Vector((v[SNX], v[SNY], v[SNZ])), k)
kd.balance(); sym_fixed = 0; done = set()
for k, v in enumerate(new):
    if k in done:
        continue
    o = Vector((v[SNX], v[SNY], v[SNZ])); p0 = v.co - o
    co, k2, dist = kd.find(Vector((-p0.x, p0.y, p0.z)))
    if k2 is None or dist > 0.003 or k2 == k:
        continue
    w = new[k2]; o2 = Vector((w[SNX], w[SNY], w[SNZ])); o2m = Vector((-o2.x, o2.y, o2.z))
    if (o - o2m).length > ASYM:
        use = o if o.length <= o2.length else o2m              # the smaller snap, applied to both (mirrored)
        for vv, oo, nn in ((v, o, use), (w, o2, Vector((-use.x, use.y, use.z)))):
            dlt = nn - oo; vv.co = vv.co + dlt; vv[SNX], vv[SNY], vv[SNZ] = nn
            for L in SK:
                vv[L] = vv[L] + dlt
        sym_fixed += 2
    done |= {k, k2}
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
SNX2, SNY2, SNZ2 = (bm.verts.layers.float.new(n) for n in ("_snx2", "_sny2", "_snz2"))
for v in bm.verts:
    v[SNX2], v[SNY2], v[SNZ2] = v[SNX], v[SNY], v[SNZ]
for nm in ("_snx", "_sny", "_snz"):
    bm.verts.layers.float.remove(bm.verts.layers.float[nm])
SNX2, SNY2, SNZ2 = (bm.verts.layers.float[n] for n in ("_snx2", "_sny2", "_snz2"))
bm.normal_update()
ngons = sum(1 for f in bm.faces if len(f.verts) > 4); nonman = sum(1 for e in bm.edges if not e.is_manifold and not e.is_boundary)
rep = {"method": __doc__.split("usage")[0].strip(), "vertices_before_after": [nv0, len(bm.verts)], "faces_before_after": [nf0, len(bm.faces)],
       "new_vertices": len(new), "snapped": snapped, "snap_max_mm": round(dmax * 1000, 2), "snaps_reverted": reverted, "asymmetric_snaps_equalised": sym_fixed, "finger_midpoints_tucked_steps": tucked,
       "ngons": ngons, "non_manifold_edges": nonman, "rest_intersecting_vertices_before_after": [inter0, inter1]}
if ngons or nonman or inter1 > inter0:
    rep["status"] = "REJECTED by guard"; REP.write_text(json.dumps(rep, indent=1)); print("DENSE", json.dumps({k: v for k, v in rep.items() if k != "method"})); sys.exit(1)
bm.to_mesh(me); me.update()
# posed fold guard: a source detail the skinning cannot carry without the skin folding through itself is not imported.
# The body is posed through the standard arm poses (anatomical elbow) and the sweep posture; intersecting triangle
# pairs within FOLD_HOPS edges of each other are local folds (contacts between body parts are further apart and are
# left to the contact correctives); snapped new vertices on their faces return to the interpolated position.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "meshy"))
from shoulder_pose_lib import arm_pose  # noqa: E402
rig = bpy.data.objects["MESHY_RIG"]; FOLD_HOPS = 4
POSES = [(8, 10, 170, 0, True), (55, 40, 70, 8, True), (105, 30, 115, 15, True), (170, 15, 175, 25, True), (17.5, 10, 40, 0, True),
         (90, 30, 175, 13.2, False), (135, 30, 175, 19.9, False), (170, 30, 175, 25, False)]
fold_reverted = 0; fold_log = []
for el, fw, elb, clv, hg in POSES:
    for _ in range(6):
        for pbn in rig.pose.bones:
            pbn.matrix_basis.identity()
        bpy.context.view_layer.update()
        for sd_ in ("l", "r"):
            arm_pose(rig, sd_, el, fw, elb, clv, hinge=hg)
        bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
        mm = bpy.data.meshes.new_from_object(body.evaluated_get(dg), depsgraph=dg); mm.calc_loop_triangles()
        PV = [v.co.copy() for v in mm.vertices]; PT = [tuple(t.vertices) for t in mm.loop_triangles]; bpy.data.meshes.remove(mm)
        bb = BVHTree.FromPolygons(PV, PT, all_triangles=True); bm.verts.ensure_lookup_table(); bad = set()
        for i, j in bb.overlap(bb):
            if i >= j or set(PT[i]) & set(PT[j]):
                continue
            seen = {PT[i][0]: 0}; q = [PT[i][0]]; tgt = set(PT[j]); near = False
            while q:
                x = q.pop(0)
                if x in tgt:
                    near = True; break
                if seen[x] >= FOLD_HOPS:
                    continue
                for e in bm.verts[x].link_edges:
                    y = e.other_vert(bm.verts[x]).index
                    if y not in seen:
                        seen[y] = seen[x] + 1; q.append(y)
            if near:
                for t in (PT[i], PT[j]):
                    for vi in t:
                        for f in bm.verts[vi].link_faces:
                            bad |= {w for w in f.verts if w[SNX2] or w[SNY2] or w[SNZ2]}
        if not bad:
            break
        for v in bad:
            off = Vector((v[SNX2], v[SNY2], v[SNZ2])); v[SNX2] = v[SNY2] = v[SNZ2] = 0.0; v.co = v.co - off; fold_reverted += 1
            for L in SK:
                v[L] = v[L] - off
        bm.to_mesh(me); me.update()
    fold_log.append([el, fw, elb, len(bad)])
for pbn in rig.pose.bones:
    pbn.matrix_basis.identity()
bpy.context.view_layer.update()
for nm in ("_snx2", "_sny2", "_snz2"):
    me.attributes.remove(me.attributes[nm])
rep["posed_fold_guard_reverted"] = fold_reverted; rep["posed_fold_guard_left_per_pose"] = fold_log
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
