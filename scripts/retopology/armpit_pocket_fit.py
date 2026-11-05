"""Close the remaining armpit pocket (source points inside the cage) - writes a NEW checkpoint.

armpit_vault_fit.py moves cage vertices into the axillary vault along their own normals; where no vertex normal points
into a pocket (the floor of the right vault) a pocket remains. Here every source point within RADIUS of the shoulder
that lies INSIDE the cage and further than GAP from it pulls its nearest cage vertex towards it: each vertex moves a
fraction STEP towards the mean of the points it is nearest to, then the moved vertices and their neighbours get a
tangential relax (umbrella with the normal component removed) so the quads spread over the new surface. A round is
kept only if it creates no self-intersection and no fold defect (cage fold > 50 deg sharper than the source); the
loop ends when the pocket stops shrinking. Then the fold defects are re-checked over the shoulders.

usage: python3.13 armpit_pocket_fit.py -- <in .blend> <out NEW .blend> <report .json>
"""
import json
import sys
from pathlib import Path

import bpy
import bmesh  # noqa: E402
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
IN, OUT, REP = Path(a[0]), Path(a[1]), Path(a[2])
if OUT.exists():
    raise FileExistsError(f"will not overwrite {OUT}")
RADIUS, GAP, STEP, ROUNDS = 0.20, 0.006, 0.5, 40
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
SRC = bpy.data.objects["HGPT_SOURCE_PROXY_Mesh_0"]; body = bpy.data.objects["HGPT_Male_Task3_Body"]
SV = np.array([v.co[:] for v in SRC.data.vertices])
sb = BVHTree.FromPolygons([Vector(p) for p in SV], [tuple(p.vertices) for p in SRC.data.polygons])
bm = bmesh.new(); bm.from_mesh(body.data); bm.verts.ensure_lookup_table()
FACES = [tuple(v.index for v in f.verts) for f in bm.faces]


def cage():
    return BVHTree.FromPolygons([v.co.copy() for v in bm.verts], FACES)


def inside(cb, p):
    n, o, d = 0, Vector(p), Vector((0.31, 0.17, 0.93)).normalized()
    while True:
        h = cb.ray_cast(o + d * 1e-5, d, 5)
        if h[0] is None:
            return n % 2 == 1
        n += 1; o = h[0]


def pocket(sg):
    cb = cage(); gh = np.array([0.22 * sg, 0.033, 1.44]); m = (np.linalg.norm(SV - gh, axis=1) < RADIUS) & (SV[:, 0] * sg > 0.06)
    out = []
    for p in SV[m]:
        loc, _, idx, d = cb.find_nearest(Vector(p))
        if d > GAP and inside(cb, p):
            out.append((p, d))
    return out


def intersections():
    tris = bm.calc_loop_triangles(); T = [tuple(l.vert.index for l in t) for t in tris]
    b = BVHTree.FromPolygons([v.co.copy() for v in bm.verts], T, all_triangles=True)
    return sum(1 for i, j in b.overlap(b) if not set(T[i]) & set(T[j]))


def fold_defects():
    bm.normal_update(); n = 0
    for e in bm.edges:
        if len(e.link_faces) != 2:
            continue
        m = (e.verts[0].co + e.verts[1].co) / 2
        if not (abs(m.x) > 0.13 and m.z > 1.2):
            continue
        f0, f1 = e.link_faces; c = np.degrees(f0.normal.angle(f1.normal, 0.0))
        if c < 50:
            continue
        s = np.degrees(sb.find_nearest(f0.calc_center_median())[1].angle(sb.find_nearest(f1.calc_center_median())[1], 0.0))
        n += int(c - s > 50)
    return n


rep = {"method": __doc__.split("usage")[0].strip(), "in": IN.name, "sides": {}}
inter0, folds0 = intersections(), fold_defects(); rep.update(self_intersections_before=inter0, fold_defects_before=folds0)
for sg in (1, -1):
    P = pocket(sg); hist = [(len(P), round(1000 * max([d for _, d in P], default=0), 1))]
    for rnd in range(ROUNDS):
        if not P:
            break
        snap = [v.co.copy() for v in bm.verts]
        cb = cage(); pull = {}
        for p, d in P:
            loc = cb.find_nearest(Vector(p))[0]
            # nearest cage VERTEX of that face region
            vi = min((v for v in bm.verts if (v.co - loc).length < 0.03), key=lambda v: (v.co - Vector(p)).length, default=None)
            if vi is not None:
                pull.setdefault(vi, []).append(Vector(p))
        moved = set()
        for v, pts in pull.items():
            tgt = sum(pts, Vector()) / len(pts); v.co = v.co.lerp(tgt, STEP); moved.add(v)
        ring = moved | {e.other_vert(v) for v in moved for e in v.link_edges}
        for _ in range(2):
            bm.normal_update(); upd = {}
            for v in ring:
                nb = [e.other_vert(v).co for e in v.link_edges]; dd = sum(nb, Vector()) / len(nb) - v.co
                upd[v] = v.co + (dd - v.normal * dd.dot(v.normal)) * 0.4
            for v, q in upd.items():
                v.co = q
        if intersections() > inter0 or fold_defects() > folds0:          # reject the round
            for v, q in zip(bm.verts, snap):
                v.co = q
            STEP_ = STEP * 0.5
            hist.append(("rejected", rnd)); break
        P2 = pocket(sg); hist.append((len(P2), round(1000 * max([d for _, d in P2], default=0), 1)))
        if len(P2) >= len(P) and rnd > 3:
            P = P2; break
        P = P2
    rep["sides"]["right" if sg > 0 else "left"] = {"history_points_maxmm": hist}
rep.update(self_intersections_after=intersections(), fold_defects_after=fold_defects())
bm.to_mesh(body.data); body.data.update()
body["ARMPIT_POCKET_FIT"] = json.dumps({k: v for k, v in rep.items() if k != "method"})
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = OUT.name; REP.write_text(json.dumps(rep, indent=1)); print("POCKET", json.dumps({k: v for k, v in rep.items() if k != "method"}))
