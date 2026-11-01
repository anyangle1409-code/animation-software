"""Add the closed-fist skin-contact keys R121_GRIP_<s> (authored by movement_trajectory_test_blender.py with
V2_TRAJ_AUTHOR_CONTACT=grip) to a COPY of a body blend, with their drive data (r121_drives.GRIP_PROP_<s> = the finger
curl they were authored at).  The source blend is not changed.

usage: python3.13 add_grip_contact_keys_blender.py -- <src.blend> <grip_contact_keys.npz> <grip_contact_keys.json> <out.blend>
"""
import json
import sys
from pathlib import Path

import bpy
import numpy as np

a = sys.argv[sys.argv.index("--") + 1:]
SRC, NPZ, JS, OUT = Path(a[0]), Path(a[1]), Path(a[2]), Path(a[3])
if OUT.exists() or OUT.resolve() == SRC.resolve():
    raise SystemExit("output must be a new file")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import r121_drives  # noqa: E402

bpy.ops.wm.open_mainfile(filepath=str(SRC))
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]; rig = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
me = body.data; n = len(me.vertices)
d = np.load(NPZ); info = json.loads(JS.read_text())
B0 = np.empty(n * 3); me.shape_keys.key_blocks[0].data.foreach_get("co", B0); B0 = B0.reshape(-1, 3)
for s in ("l", "r"):
    name = f"{r121_drives.GRIP_PREFIX}{s}"
    if name in me.shape_keys.key_blocks:
        raise SystemExit(f"{name} already exists in the source")
    kb = body.shape_key_add(name=name, from_mix=False); kb.value = 0.0
    kb.data.foreach_set("co", (B0 + d[s]).ravel())
    rig[f"{r121_drives.GRIP_PROP}_{s}"] = float(info["finger_curl_deg"][s])
me.update()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), copy=True)
print("ADDED", {s: info["finger_curl_deg"][s] for s in ("l", "r")}, "->", OUT, flush=True)
