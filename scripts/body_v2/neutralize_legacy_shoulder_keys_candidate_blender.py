"""Candidate (new blend): neutralise the legacy elevation-driven shoulder keys transferred from the old surface.

Diagnosis (press lockout on K1, high-frequency surface roughness of the upper body - |normal Laplacian minus its
neighbourhood mean| - p95):  rest 0.066 mm;  plain skinning, no corrective keys 0.117 mm (smooth back, but the armpit /
deltoid fold);  plus the legacy families S1 / S3 / S5 / S7 0.268 mm;  plus the R121 keys (K1) 0.125 mm.  The legacy
families were transferred from the old surface and add the mottled back / deltoid texture; the R121 keys, authored on
top of them, fix the folds but carry that texture.  Here every key of the given families has its offsets set to zero
(key data = basis), so the names, drives and rig properties stay and nothing else changes; the R121 arm families are
then re-authored on this clean base (r121_arm_correctives_blender.py with V2_R121_ARMKEY_REPLACE=1).

usage: python3.13 neutralize_legacy_shoulder_keys_candidate_blender.py -- <in.blend> <out.blend> [prefix ...]
       (default prefixes HGPT_S1_ HGPT_S3_ HGPT_S5_ HGPT_S7_)
"""
import json
import sys
from pathlib import Path

import bpy
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = Path(args[0]), Path(args[1])
PREFIXES = tuple(args[2:]) or ("HGPT_S1_", "HGPT_S3_", "HGPT_S5_", "HGPT_S7_")
if OUT.exists():
    raise ValueError("output must be new")
bpy.ops.wm.open_mainfile(filepath=str(SRC))
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]; me = body.data; n = len(me.vertices)
B = np.empty(n * 3); me.shape_keys.reference_key.data.foreach_get("co", B)
done = {}
for kb in me.shape_keys.key_blocks[1:]:
    if kb.name.startswith(PREFIXES):
        c = np.empty(n * 3); kb.data.foreach_get("co", c)
        done[kb.name] = round(float(np.linalg.norm((c - B).reshape(-1, 3), axis=1).max() * 1000), 2)
        kb.data.foreach_set("co", B)
rep = {"prefixes": PREFIXES, "neutralised_keys": len(done), "max_offset_mm_before": done}
body["hgpt_r121_legacy_shoulder_neutralised"] = json.dumps(rep)
me.update()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), copy=True)
print("NEUTRAL", json.dumps({"keys": len(done)}), flush=True)
