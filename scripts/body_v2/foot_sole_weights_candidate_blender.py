"""Candidate (reversible copy): plantar skin follows the foot, not the shin.

Measured on R121p: 3,622 of the 12,628 sole vertices (within 12 mm of the floor) carry shin weight, mostly under the
heel, so in the squat the heel skin turned with the dorsiflexing tibia (sole slide 19 mm, heel lift 11 mm in
movement_trajectory_test_blender.py).  The heel pad is bound to the calcaneus.  Here, for foot-weighted vertices, the
shin weight is moved to the same side's foot bone: fully at the floor, fading out by FADE_TOP above it so the ankle
blend above is unchanged.  Saves a new blend; the input is not modified.

usage: python3.13 foot_sole_weights_candidate_blender.py -- <in.blend> <out.blend> [fade_top_m (0.030)]
"""
import json
import sys
from pathlib import Path

import bpy

args = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = Path(args[0]), Path(args[1])
FADE_LO, FADE_TOP = 0.012, float(args[2]) if len(args) > 2 else 0.030
if OUT.exists():
    raise ValueError("output must be new")
bpy.ops.wm.open_mainfile(filepath=str(SRC))
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]; me = body.data
G = {g.name: g for g in body.vertex_groups}
z0 = min(v.co.z for v in me.vertices)


def ss(x):
    x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)


moved = {"l": 0, "r": 0}; total = 0.0
for v in me.vertices:
    h = v.co.z - z0
    if h > FADE_TOP:
        continue
    w = {body.vertex_groups[g.group].name: g.weight for g in v.groups}
    for s in ("l", "r"):
        sh, ft = w.get(f"shin_{s}", 0.0), w.get(f"foot_{s}", 0.0) + w.get(f"toe_{s}", 0.0)
        if sh <= 0.0 or ft <= 0.0:
            continue
        keep = ss((h - FADE_LO) / (FADE_TOP - FADE_LO))          # 0 on the sole -> 1 at FADE_TOP
        d = sh * (1.0 - keep)
        if d <= 1e-6:
            continue
        G[f"shin_{s}"].add([v.index], sh - d, "REPLACE")
        G[f"foot_{s}"].add([v.index], w.get(f"foot_{s}", 0.0) + d, "REPLACE")
        moved[s] += 1; total += d
rep = {"fade_m": [FADE_LO, FADE_TOP], "vertices_changed": moved, "weight_moved_total": round(total, 2)}
body["hgpt_r121_sole_weights"] = json.dumps(rep)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), copy=True)
print("SOLE", json.dumps(rep), flush=True)
