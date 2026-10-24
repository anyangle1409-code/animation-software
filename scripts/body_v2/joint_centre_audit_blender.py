"""Read-only joint-centre audit of a body_v2 blend: rig pivots against skin-derived joint centres.

ISB / clinical joint-centre definitions that need no regression coefficients (Wu et al. 2002, 2005):
  knee  = midpoint of the medial and lateral femoral epicondyles
  ankle = midpoint of the medial and lateral malleoli
  elbow = midpoint of the medial and lateral humeral epicondyles
  wrist = midpoint of the radial and ulnar styloids
Each bony prominence is approximated on the skin as the most medial / most lateral skin point of that limb within a
band of +-BAND mm (along the limb) around the rig pivot; the prominences lie under thin skin, so the skin extreme is the
usual palpation point.  Reported: pivot minus skin midpoint (lateral +, anterior +, up +, mm), the medio-lateral
width, and the pivot's position across the antero-posterior depth (0 = posterior skin, 1 = anterior skin).
The hip has no skin proxy (deep joint); the blend's LM_hip_bone_*__HJC (R41 positions) is listed for reference only.
Nothing is saved.

usage: python3.13 joint_centre_audit_blender.py -- <body.blend> <out.json>
"""
import json
import sys
from pathlib import Path

import bpy
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = Path(args[0]), Path(args[1])
bpy.ops.wm.open_mainfile(filepath=str(SRC))
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]; rig = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
me = body.data
P = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", P); P = P.reshape(-1, 3)
GN = [g.name for g in body.vertex_groups]
W = {}
for v in me.vertices:
    for g in v.groups:
        W.setdefault(GN[g.group], np.zeros(len(P)))[v.index] = g.weight
B = rig.data.bones
BAND = 0.025

JOINTS = {  # joint: (pivot bone and end, limb-axis bones (proximal, distal), vertex groups of the limb near the joint)
    "knee": ("shin_{s}", "head", ("thigh_{s}", "shin_{s}"), ("thigh_{s}", "shin_{s}")),
    "ankle": ("foot_{s}", "head", ("shin_{s}", "shin_{s}"), ("shin_{s}", "foot_{s}")),
    "elbow": ("forearm_{s}", "head", ("upperarm_{s}", "forearm_{s}"), ("upperarm_{s}", "forearm_{s}", "forearm_tw0_{s}")),
    "wrist": ("hand_{s}", "head", ("forearm_tw1_{s}", "forearm_tw1_{s}"), ("forearm_tw1_{s}", "hand_{s}")),
}
REP = {"source": SRC.name, "band_mm": BAND * 1000, "joints": {}}
for j, (pb, end, axb, groups) in JOINTS.items():
    for s in ("l", "r"):
        lat = 1.0 if B[f"upperarm_{s}"].head_local.x > 0 else -1.0
        piv = np.array(getattr(B[pb.format(s=s)], f"{end}_local"))
        a0, a1 = B[axb[0].format(s=s)], B[axb[1].format(s=s)]
        ax = np.array(a1.tail_local - a0.head_local); ax /= np.linalg.norm(ax)
        w = sum(W.get(g.format(s=s), np.zeros(len(P))) for g in groups)
        m = (w > 0.3) & (np.abs((P - piv) @ ax) < BAND) & (np.sign(P[:, 0]) == lat)
        if m.sum() < 20:
            REP["joints"][f"{j}_{s}"] = {"error": "too few skin points", "n": int(m.sum())}
            continue
        Q = P[m]
        lat_pt, med_pt = Q[np.argmax(Q[:, 0] * lat)], Q[np.argmin(Q[:, 0] * lat)]
        mid = (lat_pt + med_pt) / 2
        d = piv - mid
        ant_skin, post_skin = Q[:, 1].min(), Q[:, 1].max()             # anterior = -y
        ap = (post_skin - piv[1]) / (post_skin - ant_skin)
        REP["joints"][f"{j}_{s}"] = {
            "pivot_m": [round(float(x), 4) for x in piv], "skin_mid_m": [round(float(x), 4) for x in mid],
            "pivot_minus_mid_mm": {"lateral": round(float(d[0] * lat * 1000), 1), "anterior": round(float(-d[1] * 1000), 1),
                                   "up": round(float(d[2] * 1000), 1)},
            "ml_width_mm": round(float(abs(lat_pt[0] - med_pt[0]) * 1000), 1),
            "ap_depth_mm": round(float((post_skin - ant_skin) * 1000), 1),
            "pivot_ap_fraction_from_posterior": round(float(ap), 3),
            "prominence_ap_mm_from_posterior": {"lateral": round(float((post_skin - lat_pt[1]) * 1000), 1),
                                                "medial": round(float((post_skin - med_pt[1]) * 1000), 1)},
            "skin_points": int(m.sum())}
hjc = {}
for o in bpy.data.objects:
    if o.name.startswith("LM_hip_bone_") and o.name.endswith("__HJC"):
        hjc[o.name] = [round(float(x), 4) for x in o.matrix_world.translation]
for s in ("l", "r"):
    hjc[f"rig thigh_{s} head"] = [round(float(x), 4) for x in B[f"thigh_{s}"].head_local]
REP["hip_reference_only"] = hjc
OUT.write_text(json.dumps(REP, indent=1))
for k, v in REP["joints"].items():
    print("JOINT", k, json.dumps({x: v[x] for x in ("pivot_minus_mid_mm", "ml_width_mm", "ap_depth_mm", "pivot_ap_fraction_from_posterior")} if "error" not in v else v))
print("HIP", json.dumps(hjc))
