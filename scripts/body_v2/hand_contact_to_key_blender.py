"""Candidate fix: the hand-on-thigh part of the rest-contact pass must be transient, not baked into the basis.

rest_contact_candidate_blender.py flattened the outer thighs (and the hanging hands) where they met at the rest pose -
up to 18.9 mm on ~1,640 thigh vertices - and stored it in the basis, so the dent stayed when the hands moved away (curl,
press).  Here the part below SPLIT_H (stature fraction; hands, wrists, thighs, hips) is taken out of the basis and every
key, and stored instead as keys R121_REST_HANDCONTACT_<s> (split by side), which r121_drives drives from the arm's
humerothoracic elevation: 1 at the rest elevation, 0 eight degrees above it.  The small inner-arm / chest flattening
(<= 5 mm, above SPLIT_H) stays in the basis.

usage: python3.13 hand_contact_to_key_blender.py -- <with_contact.blend> <before_contact.blend> <r57src> <out.blend>
(<before_contact.blend> must share the topology; its basis gives the pre-contact positions)
"""
import json
import sys
from pathlib import Path

import bpy
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:]
WITH, BEFORE, ROOT, OUT = Path(args[0]), Path(args[1]), Path(args[2]), Path(args[3])
SPLIT_H = 0.52
if OUT.exists():
    raise ValueError("output must be new")
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "scripts/anatomy_fit"), str(Path(__file__).resolve().parent)]


def basis(p):
    bpy.ops.wm.open_mainfile(filepath=str(p))
    me_ = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"].data
    P = np.empty(len(me_.vertices) * 3); me_.vertices.foreach_get("co", P)
    return P.reshape(-1, 3)


A = basis(BEFORE)
bpy.ops.wm.open_mainfile(filepath=str(WITH))
import build_original_movement_benchmarks_blender as bench  # noqa: E402
import original_v1_review_candidate_drives as drives  # noqa: E402
import r121_drives  # noqa: E402

body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]; rig = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
me = body.data; n = len(me.vertices)
B = np.empty(n * 3); me.vertices.foreach_get("co", B); B = B.reshape(-1, 3)
if len(A) != n:
    raise ValueError("topology differs")
z0 = A[:, 2].min(); H = A[:, 2].max() - z0
low = ((A[:, 2] - z0) / H) < SPLIT_H
D = (B - A) * low[:, None]
ref = me.shape_keys.reference_key
for kb in me.shape_keys.key_blocks:
    c = np.empty(n * 3); kb.data.foreach_get("co", c); kb.data.foreach_set("co", (c.reshape(-1, 3) - D).ravel())
me.vertices.foreach_set("co", (B - D).ravel()); me.update()
for s in ("r", "l"):
    side = np.sign(A[:, 0]) == np.sign(rig.data.bones[f"upperarm_{s}"].head_local.x)
    kb = body.shape_key_add(name=f"{r121_drives.HANDCONTACT_PREFIX}{s}", from_mix=False); kb.value = 0.0
    kb.data.foreach_set("co", (B - D + D * side[:, None]).ravel())
bench._reset(rig); bpy.context.view_layer.update()
for s in ("l", "r"):
    rig[f"{r121_drives.HANDCONTACT_PROP}_{s}"] = float(drives.elevation_deg(rig, s))
rep = {"split_stature_fraction": SPLIT_H, "moved_to_keys_vertices": int((np.linalg.norm(D, axis=1) > 1e-4).sum()),
       "max_mm": round(float(np.linalg.norm(D, axis=1).max() * 1000), 2),
       "rest_elevation_deg": {s: round(rig[f"{r121_drives.HANDCONTACT_PROP}_{s}"], 2) for s in ("l", "r")}}
body["hgpt_r121_hand_contact_key"] = json.dumps(rep)
for kb in me.shape_keys.key_blocks[1:]:
    kb.value = 0.0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), copy=True)
print("HANDCONTACT", json.dumps(rep), flush=True)
