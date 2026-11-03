"""Worksheet measurements (mm, world space, z up, floor = lowest vertex) of a body mesh and its rig, in the file's
saved pose.  Rig names: canonical (Body v2) or MPFB game_engine.  Sections use the evaluated mesh; circumferences are
convex-hull perimeters of a horizontal slice (tape-measure approximation).  Landmarks that this method cannot locate
are reported UNKNOWN.  usage: python3.13 measure_worksheet.py -- <blend> <kind canonical|mpfb> <label> <out.json>"""
import hashlib, json, sys
from pathlib import Path
import bpy
import numpy as np
from scipy.spatial import ConvexHull
a = sys.argv[sys.argv.index("--") + 1:]
blend, kind, label, out = a
bpy.ops.wm.open_mainfile(filepath=blend)
arms = [o for o in bpy.data.objects if o.type == "ARMATURE"]
if kind == "canonical":
    body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]; rig = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
    B = dict(ua="upperarm_{}", fa="forearm_{}", hand="hand_{}", thigh="thigh_{}", shin="shin_{}", foot="foot_{}")
    armk = ("upperarm", "forearm", "hand", "thumb", "index", "middle", "ring", "pinky", "metacarpal")
else:
    body = max((o for o in bpy.data.objects if o.type == "MESH"), key=lambda o: len(o.data.vertices)); rig = arms[0]
    B = dict(ua="upperarm_{}", fa="lowerarm_{}", hand="hand_{}", thigh="thigh_{}", shin="calf_{}", foot="foot_{}")
    armk = ("upperarm", "lowerarm", "hand", "thumb", "index", "middle", "ring", "pinky")
dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); m = ev.to_mesh()
V = np.empty(len(m.vertices) * 3); m.vertices.foreach_get("co", V); V = V.reshape(-1, 3)
mw = np.array(body.matrix_world); V = V @ mw[:3, :3].T + mw[:3, 3]
GN = {g.index: g.name for g in body.vertex_groups}; armw = np.zeros(len(V)); handw = np.zeros(len(V))
for v in m.vertices:
    for g in v.groups:
        nm = GN.get(g.group, "")
        if any(k in nm for k in armk): armw[v.index] += g.weight
        if any(k in nm for k in ("hand", "thumb", "index", "middle", "ring", "pinky", "metacarpal")): handw[v.index] += g.weight
ev.to_mesh_clear()
z0 = V[:, 2].min(); H = V[:, 2].max() - z0; h = (V[:, 2] - z0) / H; trunk = armw < 0.3
P = lambda nm: np.array(rig.matrix_world @ rig.pose.bones[nm].head)
mm = lambda x: None if x is None else round(float(x) * 1000, 1)


def sl(f, sel, tol=0.003):
    return sel & (np.abs(h - f) < tol)


def circ(pts):
    if len(pts) < 5: return None
    hull = ConvexHull(pts[:, :2]); q = pts[hull.vertices, :2]
    return float(np.linalg.norm(q - np.roll(q, 1, 0), axis=1).sum())


r = {}
r["stature_barefoot"] = mm(H)
r["head_height_vertex_to_chin"] = "UNKNOWN (no chin landmark in this method)"
band = (h > 0.74) & (h < 0.82); r["bideltoid_breadth"] = mm(np.ptp(V[band, 0]))
ch = sl(0.72, trunk); r["upper_chest_breadth"] = mm(np.ptp(V[ch, 0])); r["chest_depth"] = mm(np.ptp(V[ch, 1])); r["chest_circumference"] = mm(circ(V[ch]))
best = None
for f in np.arange(0.57, 0.65, 0.005):
    s = sl(f, trunk); w = np.ptp(V[s, 0]) if s.sum() > 5 else 9
    if best is None or w < best[0]: best = (w, f)
ws = sl(best[1], trunk); r["bare_waist_breadth"] = mm(best[0]); r["waist_depth"] = mm(np.ptp(V[ws, 1])); r["waist_circumference"] = mm(circ(V[ws]))
r["waist_plane_fraction_of_stature"] = round(float(best[1]), 3)
hb = (h > 0.47) & (h < 0.54) & trunk; r["hip_breadth"] = mm(np.ptp(V[hb, 0]))
r["shoulder_waist_ratio_3d"] = round(r["bideltoid_breadth"] / r["bare_waist_breadth"], 3)
gh = P(B["ua"].format("l")); r["shoulder_height_GH_centre"] = mm(gh[2] - z0)
r["biacromial_breadth"] = "UNKNOWN (no acromion landmark; GH-centre spacing given instead)"
r["GH_centre_spacing"] = mm(abs(P(B["ua"].format("l"))[0] - P(B["ua"].format("r"))[0]))
r["wrist_height"] = mm(P(B["hand"].format("l"))[2] - z0)
mid = (np.abs(V[:, 0]) < 0.006) & (h > 0.35) & (h < 0.6); cand = V[mid & trunk]
r["crotch_height"] = mm(cand[:, 2].min() - z0) if len(cand) else "UNKNOWN"
r["hip_joint_height"] = mm(P(B["thigh"].format("l"))[2] - z0)
ua = np.linalg.norm(P(B["fa"].format("l")) - P(B["ua"].format("l"))); fa = np.linalg.norm(P(B["hand"].format("l")) - P(B["fa"].format("l")))
r["upperarm_length"] = mm(ua); r["forearm_length"] = mm(fa)
hv = V[(handw > 0.5) & (V[:, 0] * np.sign(P(B["hand"].format("l"))[0]) > 0)]
r["hand_length"] = mm(np.linalg.norm(hv - P(B["hand"].format("l")), axis=1).max()) if len(hv) else "UNKNOWN"
r["arm_length_GH_to_fingertip"] = mm(np.linalg.norm(hv - gh, axis=1).max()) if len(hv) else "UNKNOWN"
r["thigh_length"] = mm(np.linalg.norm(P(B["shin"].format("l")) - P(B["thigh"].format("l"))))
r["lowerleg_length"] = mm(np.linalg.norm(P(B["foot"].format("l")) - P(B["shin"].format("l"))))
sg = np.sign(P(B["foot"].format("l"))[0]); legs = (V[:, 0] * sg > 0) & trunk
fv = V[legs & (h < 0.06)]; r["foot_length"] = mm(np.ptp(fv[:, 1])) if len(fv) else "UNKNOWN"
for nm, f in (("thigh_circumference_upper", 0.44), ("thigh_circumference_lower", 0.37), ("knee_circumference", 0.285)):
    r[nm] = mm(circ(V[sl(f, legs)]))
best = max((circ(V[sl(f, legs)]) or 0, f) for f in np.arange(0.17, 0.25, 0.005)); r["calf_circumference_max"] = mm(best[0])
low = min((circ(V[sl(f, legs)]) or 9, f) for f in np.arange(0.05, 0.09, 0.005)); r["ankle_circumference_min"] = mm(low[0])
hsh = hashlib.sha256(Path(blend).read_bytes()).hexdigest()
res = {"label": label, "kind": kind, "blend": Path(blend).name, "blend_sha256": hsh, "pose": "as saved in the file",
       "rig": rig.name, "body": body.name, "vertices_evaluated": int(len(V)), "measures_mm": r}
Path(out).write_text(json.dumps(res, indent=1)); print("WS", json.dumps(res))
