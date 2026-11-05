"""Proportions: current body vs the approved source, in the shared rest pose (read-only).

Girths are measured like a tape measure: the convex hull perimeter of the mesh cross-section in a plane. Trunk girths are
taken in horizontal planes (the slice loop around the body midline only); limb girths in planes perpendicular to the
bone at a fraction of its length (rig bones are shared, so both meshes are cut by the same planes). Lengths/breadths from
the mesh extents. Both meshes are measured identically.

usage: python3.13 proportion_compare_blender.py -- <bound .blend> <retopo checkpoint with source proxy> <report .json>
"""
import json
import sys
from pathlib import Path

import bpy
import bmesh  # noqa: E402
import numpy as np
from mathutils import Vector
from scipy.spatial import ConvexHull

a = sys.argv[sys.argv.index("--") + 1:]
IN, SRCBLEND, REP = Path(a[0]), Path(a[1]), Path(a[2])
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
with bpy.data.libraries.load(str(SRCBLEND), link=False) as (src, dst):
    dst.objects = ["HGPT_SOURCE_PROXY_Mesh_0"]
srcob = dst.objects[0]; body = bpy.data.objects["MESHY_BODY"]; rig = bpy.data.objects["MESHY_RIG"]


def world_verts(ob):
    return np.array([ob.matrix_world @ v.co for v in ob.data.vertices])


def section(ob, co, no):
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.transform(ob.matrix_world)
    r = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=co, plane_no=no)
    segs = [(e.verts[0].co.copy(), e.verts[1].co.copy()) for e in r["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
    bm.free(); return segs


def loops(segs):
    key = lambda p: (round(p.x, 5), round(p.y, 5), round(p.z, 5)); adj = {}; pos = {}
    for p, q in segs:
        a_, b_ = key(p), key(q); pos[a_] = p; pos[b_] = q
        adj.setdefault(a_, []).append(b_); adj.setdefault(b_, []).append(a_)
    seen = set(); out = []
    for s in adj:
        if s in seen:
            continue
        comp = []; st = [s]
        while st:
            x = st.pop()
            if x in seen:
                continue
            seen.add(x); comp.append(pos[x]); st += adj[x]
        out.append(comp)
    return out


def girth(ob, co, no, pick, radius=None):
    co = Vector(co); no = Vector(no).normalized(); L = loops(section(ob, co, no))
    if not L:
        return None
    L = [l for l in L if len(l) > 8]; c = min(L, key=lambda l: (sum(l, Vector()) / len(l) - Vector(pick)).length)
    if radius:                                                    # limbs: only the section around the bone (the plane can
        c = [p for l in L for p in l if (p - Vector(pick)).length < radius]   # also cut the trunk in the A-pose)
    u = no.orthogonal().normalized(); v = no.cross(u); P = np.array([[(p - co).dot(u), (p - co).dot(v)] for p in c])
    h = ConvexHull(P); return round(float(h.area) * 1000, 1)        # 2D hull 'area' is the perimeter


def bone(name, t):
    b = rig.data.bones[name]; h = rig.matrix_world @ b.head_local; tl = rig.matrix_world @ b.tail_local
    return h + (tl - h) * t, (tl - h).normalized()


out = {}
for who, ob in (("source", srcob), ("current", body)):
    V = world_verts(ob); r = {}
    r["height_mm"] = round(float(V[:, 2].max() - V[:, 2].min()) * 1000, 1)
    sh = V[(V[:, 2] > 1.40) & (V[:, 2] < 1.52)]; r["shoulder_breadth_deltoids_mm"] = round(float(np.ptp(sh[:, 0])) * 1000, 1)
    hip = V[(V[:, 2] > 0.85) & (V[:, 2] < 0.98) & (np.abs(V[:, 0]) < 0.22)]; r["hip_breadth_mm"] = round(float(np.ptp(hip[:, 0])) * 1000, 1)
    zs = np.linspace(0.95, 1.40, 46); widths = []
    for z in zs:
        s = V[(np.abs(V[:, 2] - z) < 0.005) & (np.abs(V[:, 0]) < 0.20)]
        widths.append(np.ptp(s[:, 0]) if len(s) else 9)
    zw = float(zs[int(np.argmin(widths[:20]))]); r["narrowest_waist_level_z_mm"] = round(zw * 1000)
    zw = 1.08                                                   # girths compared at the SAME height on both meshes
    for nm, z in (("chest_girth_mm", 1.32), ("waist_girth_z1080_mm", zw), ("hip_girth_mm", 0.90)):
        r[nm] = girth(ob, (0, 0, z), (0, 0, 1), (0, 0.02, z))
    for nm, bn, t in (("upper_arm_girth_r_mm", "upperarm_r", 0.60), ("upper_arm_girth_l_mm", "upperarm_l", 0.60),
                      ("forearm_girth_r_mm", "forearm_r", 0.25), ("forearm_girth_l_mm", "forearm_l", 0.25),
                      ("thigh_girth_r_mm", "thigh_r", 0.30), ("thigh_girth_l_mm", "thigh_l", 0.30),
                      ("calf_girth_r_mm", "shin_r", 0.30), ("calf_girth_l_mm", "shin_l", 0.30), ("neck_girth_mm", "neck", 0.5)):
        if bn not in rig.data.bones:
            continue
        co, d = bone(bn, t); r[nm] = girth(ob, co, d, co, radius=0.07 if bn.startswith(("upperarm", "forearm")) else 0.12)
    out[who] = r
diff = {k: (round(out["current"][k] - out["source"][k], 1) if isinstance(out["source"].get(k), (int, float)) and out["current"].get(k) is not None else None) for k in out["source"]}
pct = {k: (round(100 * diff[k] / out["source"][k], 2) if diff[k] is not None and out["source"][k] else None) for k in out["source"]}
rep = {"method": __doc__.split("usage")[0].strip(), "source": out["source"], "current": out["current"], "diff_mm": diff, "diff_pct": pct}
REP.write_text(json.dumps(rep, indent=1))
for k in out["source"]:
    print("H %-30s source %8s  current %8s  diff %6s mm (%s %%)" % (k, out["source"][k], out["current"][k], diff[k], pct[k]))
