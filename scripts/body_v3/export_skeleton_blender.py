"""Export the canonical skeleton's rest frames (armature space = world for our rig) to JSON for the body_v3 builder.
usage: python3.13 export_skeleton_blender.py -- <blend with the canonical rig> <out.json>"""
import json
import sys
from pathlib import Path

import bpy

a = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "body_v2"))
import character_profile  # noqa: E402
_, rn = character_profile.blender_names()
rig = bpy.data.objects[rn]; mw = rig.matrix_world
out = {}
for b in rig.data.bones:
    m = mw @ b.matrix_local
    out[b.name] = {"head": list(mw @ b.head_local), "tail": list(mw @ b.tail_local), "matrix": [list(r) for r in m],
                   "parent": b.parent.name if b.parent else None}
Path(a[1]).write_text(json.dumps({"rig": rn, "bones": out}, indent=1)); print("SKEL", len(out))
