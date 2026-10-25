"""Candidate (new blend): move the rig's elbow or ankle pivot to the skin-landmark joint centre, nothing else.

joint_centre_audit_blender.py measured the rig's elbow pivot (forearm head) on R121p about 17-18 mm posterior and 22 mm
above the midpoint of the skin epicondyles (the ISB elbow centre, Wu et al. 2005).  Here, on a copy, each forearm bone is
disconnected from its upper arm and its head moved by FRACTION of that offset, which is re-measured on this blend with
the audit's method (in world axes) and mirror-averaged so the rig stays symmetric.  The upper arm, the forearm tail
(wrist), the mesh, the weights and every shape key are unchanged, so the rest pose is identical; only the elbow's rotation centre moves.  This is a skeleton-shift TEST: the
validated skeleton is not changed, and adopting it would be an owner decision.

The ankle works the same way: the foot bone's head is moved to the midpoint of the malleoli (skin extremes of the
shin / foot within +-BAND of the pivot); the audit measured the ankle pivot 16 mm above the malleolar line.

usage: python3.13 pivot_shift_candidate_blender.py -- <in.blend> <out.blend> [fraction (1.0)] [elbow|ankle]
"""
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = Path(args[0]), Path(args[1])
FRACTION = float(args[2]) if len(args) > 2 else 1.0
JOINT = args[3] if len(args) > 3 else "elbow"
# joint: (moved bone (its head is the pivot), proximal bone, vertex groups of the limb near the joint)
J = {"elbow": ("forearm_{s}", "upperarm_{s}", ("upperarm_{s}", "forearm_{s}")),
     "ankle": ("foot_{s}", "shin_{s}", ("shin_{s}", "foot_{s}"))}[JOINT]
BAND = 0.025
if OUT.exists():
    raise ValueError("output must be new")
bpy.ops.wm.open_mainfile(filepath=str(SRC))
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]; rig = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
me = body.data
P = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", P); P = P.reshape(-1, 3)
P = (np.array(body.matrix_world) @ np.c_[P, np.ones(len(P))].T).T[:, :3]
GN = [g.name for g in body.vertex_groups]
W = {}
for v in me.vertices:
    for g in v.groups:
        W.setdefault(GN[g.group], np.zeros(len(P)))[v.index] = g.weight
B = rig.data.bones
MWr = np.array(rig.matrix_world)


def wpt(v):
    return (MWr @ np.r_[np.array(v), 1.0])[:3]


def epicondyle_mid(s):
    """the audit's method: most medial / lateral skin points of the arm within +-BAND of the pivot, along the limb"""
    mv, px, groups = J[0].format(s=s), J[1].format(s=s), [g.format(s=s) for g in J[2]]
    piv = wpt(B[mv].head_local)
    ax = wpt(B[px].head_local) - piv; ax /= np.linalg.norm(ax)                 # along the proximal segment
    limb = sum(W.get(g, 0) for g in groups) > 0.5
    near = limb & (np.abs((P - piv) @ ax) < BAND)
    lat = np.array([1.0 if piv[0] > 0 else -1.0, 0, 0]); lat -= ax * (lat @ ax); lat /= np.linalg.norm(lat)
    q = P[near]; d = q @ lat
    mid = 0.5 * (q[d.argmax()] + q[d.argmin()])
    return piv, mid


rep = {"joint": JOINT, "fraction": FRACTION}
moves = {}
for s in ("l", "r"):
    piv, mid = epicondyle_mid(s)
    moves[s] = (mid - piv) * FRACTION
    rep[s] = {"pivot_m": [round(float(x), 4) for x in piv], "epicondyle_mid_m": [round(float(x), 4) for x in mid],
              "shift_mm": [round(float(x) * 1000, 1) for x in moves[s]]}
avg = 0.5 * (moves["r"] + moves["l"] * np.array([-1.0, 1.0, 1.0]))   # mirror average: keep the rig symmetric
moves = {"r": avg, "l": avg * np.array([-1.0, 1.0, 1.0])}
for s in ("l", "r"):
    rep[s]["shift_mm_applied_mirror_avg"] = [round(float(x) * 1000, 1) for x in moves[s]]
bpy.context.view_layer.objects.active = rig
for ob in bpy.context.selected_objects:
    ob.select_set(False)
rig.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")
eb = rig.data.edit_bones
inv = np.linalg.inv(MWr)
for s in ("l", "r"):
    name = J[0].format(s=s)
    fb = eb[name]
    fb.use_connect = False
    fb.head = Vector((inv @ np.r_[wpt(B[name].head_local) + moves[s], 1.0])[:3])
bpy.ops.object.mode_set(mode="OBJECT")
for s in ("l", "r"):
    rep[s]["new_pivot_m"] = [round(float(x), 4) for x in wpt(rig.data.bones[J[0].format(s=s)].head_local)]
body[f"hgpt_r121_{JOINT}_pivot_shift"] = json.dumps(rep)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), copy=True)
print("PIVOT", json.dumps(rep), flush=True)
