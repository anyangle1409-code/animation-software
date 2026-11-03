"""Measure an MPFB benchmark body against the owner's Option 5 guide table (cm), stand pose as saved.

Circumferences are convex-hull perimeters of slices (tape-measure approximation):
  trunk (chest / underbust / waist / hip) - horizontal slices of non-arm skin; chest = max 0.69-0.76 H, underbust (female)
  = min 0.64-0.69 H, waist = min 0.57-0.66 H, hip = max 0.45-0.54 H;
  limbs - slices perpendicular to the bone: upper arm max over 30-70 % of the humerus, thigh max over 5-40 % of the femur,
  calf max over 15-50 % of the tibia (one side, the left).
Biacromial ~ distance between the clavicle bone tails (the rig's acromion end); bideltoid = outer skin width 0.74-0.82 H.
Inseam = crotch height (lowest midline skin between the legs).  usage: python3.13 measure_guide.py -- <blend> <sex> <out.json>
"""
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from scipy.spatial import ConvexHull

a = sys.argv[sys.argv.index("--") + 1:]
blend, sex, outp = a
bpy.ops.wm.open_mainfile(filepath=blend)
rig = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
body = max((o for o in bpy.data.objects if o.type == "MESH" and "FLOOR" not in o.name and not o.hide_render),
           key=lambda o: len(o.data.vertices))
dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); m = ev.to_mesh()
V = np.empty(len(m.vertices) * 3); m.vertices.foreach_get("co", V); V = V.reshape(-1, 3)
mw = np.array(body.matrix_world); V = V @ mw[:3, :3].T + mw[:3, 3]
GN = {g.index: g.name for g in body.vertex_groups}; G = {}
for v in m.vertices:
    for g in v.groups:
        nm = GN.get(g.group)
        if nm:
            G.setdefault(nm, np.zeros(len(V)))[v.index] = g.weight
ev.to_mesh_clear()
n = len(V); z0 = V[:, 2].min(); H = V[:, 2].max() - z0; h = (V[:, 2] - z0) / H
gw = lambda *ks: sum((w for nm, w in G.items() if any(k in nm for k in ks)), np.zeros(n))
armw = gw("upperarm", "lowerarm", "hand", "thumb", "index", "middle", "ring", "pinky")
P = lambda nm, tail=False: np.array(rig.matrix_world @ (rig.pose.bones[nm].tail if tail else rig.pose.bones[nm].head))


def perim2(pts):
    if len(pts) < 6:
        return 0.0
    q = pts[ConvexHull(pts).vertices]; return float(np.linalg.norm(q - np.roll(q, 1, 0), axis=1).sum())


def hslice(f, mask, tol=0.0025):
    s = mask & (np.abs(h - f) < tol); return perim2(V[s, :2]) if s.sum() > 6 else 0.0


def bslice(bone, child_head, t, mask, tol=0.003, rmax=0.10):
    hd, tl = P(bone), P(child_head); ax = tl - hd; L = np.linalg.norm(ax); ax /= L
    rel = V - hd; d = rel @ ax - t * L; rad = np.linalg.norm(rel - np.outer(rel @ ax, ax), axis=1)
    s = mask & (np.abs(d) < tol) & (rad < rmax)
    if s.sum() < 6:
        return 0.0
    u = np.cross(ax, [0, 0, 1.0]); u = u / np.linalg.norm(u) if np.linalg.norm(u) > 1e-6 else np.array([1.0, 0, 0]); w = np.cross(ax, u)
    r = rel[s]; return perim2(np.c_[r @ u, r @ w])


trunk = armw < 0.3
cm = lambda x: round(float(x) * 100, 1)
r = {"height": cm(H)}
r["biacromial_breadth_approx"] = cm(abs(P("clavicle_l", True)[0] - P("clavicle_r", True)[0]))
band = (h > 0.74) & (h < 0.82); r["bideltoid_breadth"] = cm(np.ptp(V[band, 0]))
r["chest_circumference"] = cm(max(hslice(f, trunk) for f in np.arange(0.69, 0.765, 0.005)))
if sex == "female":
    r["underbust_circumference"] = cm(min(x for x in (hslice(f, trunk) for f in np.arange(0.64, 0.695, 0.005)) if x > 0))
r["waist_circumference"] = cm(min(x for x in (hslice(f, trunk) for f in np.arange(0.57, 0.665, 0.005)) if x > 0))
r["hip_circumference"] = cm(max(hslice(f, trunk) for f in np.arange(0.45, 0.545, 0.005)))
hb = max(np.ptp(V[trunk & (np.abs(h - f) < 0.0025), 0]) for f in np.arange(0.45, 0.545, 0.005))
r["hip_breadth"] = cm(hb)
ua = G.get("upperarm_l", np.zeros(n)) > 0.5
r["upper_arm_circumference"] = cm(max(bslice("upperarm_l", "lowerarm_l", t, ua, rmax=0.08) for t in np.arange(0.3, 0.71, 0.04)))
th = G.get("thigh_l", np.zeros(n)) > 0.5
r["thigh_circumference"] = cm(max(bslice("thigh_l", "calf_l", t, th, rmax=0.14) for t in np.arange(0.05, 0.41, 0.03)))
ca = G.get("calf_l", np.zeros(n)) > 0.5
r["calf_circumference"] = cm(max(bslice("calf_l", "foot_l", t, ca, rmax=0.09) for t in np.arange(0.15, 0.51, 0.03)))
yc = (P("thigh_l")[1] + P("thigh_r")[1]) / 2   # perineum: midline skin at the hip joints' depth (not the genital bulge in front)
thw = G.get("thigh_l", np.zeros(n)) + G.get("thigh_r", np.zeros(n))   # the touching inner thighs are not the crotch
mid = (np.abs(V[:, 0]) < 0.008) & (h > 0.35) & (h < 0.6) & trunk & (thw < 0.5) & (np.abs(V[:, 1] - yc) < 0.03)
r["inseam_crotch_height"] = cm(V[mid, 2].min() - z0) if mid.any() else None
r["shoulder_hip_ratio_bideltoid"] = round(r["bideltoid_breadth"] / r["hip_breadth"], 3)
r["shoulder_hip_ratio_biacromial"] = round(r["biacromial_breadth_approx"] / r["hip_breadth"], 3)
Path(outp).write_text(json.dumps({"blend": Path(blend).name, "sex": sex, "cm": r}, indent=1)); print("GUIDE", json.dumps(r))
