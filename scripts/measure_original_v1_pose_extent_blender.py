"""Read-only: world-space bounding box of the posed bare body for the given poses (never saves the .blend).

blender --background --factory-startup <candidate.blend> --python-exit-code 1 --python scripts/measure_original_v1_pose_extent_blender.py -- <out.json> <pose[,pose...]>

Used to size a fixed review frame (centre + orthographic scale) so a pose is not cropped; it never auto-fits a render.
"""
import json
import sys
import tempfile
from pathlib import Path

import bpy
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:]
out, poses = Path(args[0]), args[1].split(",")
ps = Path(__file__).with_name("pose_test_original_v1_o4_candidate_blender.py")
src = ps.read_text(encoding="utf-8")
saved = sys.argv
sys.argv = ["blender", "--", tempfile.mkdtemp(), ""]
ns = {"__name__": "pose_defs", "__file__": ps.name}
exec(compile(src[:src.index("# ---------------------------------------------------------------- metrics")], "defs", "exec"), ns)
sys.argv = saved
rig, body, POSES, reset, upd = ns["rig"], ns["body"], ns["POSES"], ns["reset"], ns["upd"]
mask = body.modifiers.get("HGPT_DRESSED_MASK")
if mask is not None:
    mask.show_viewport = False
res = {}
for name in poses:
    reset()
    rig.location = (0, 0, 0)
    ns["HANDLE"].clear()
    POSES[name]()
    upd()
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    P = np.array([(ev.matrix_world @ v.co)[:] for v in ev.data.vertices])
    lo, hi = P.min(axis=0), P.max(axis=0)
    res[name] = {"min": [round(float(x), 4) for x in lo], "max": [round(float(x), 4) for x in hi],
                 "centre": [round(float(x), 4) for x in (lo + hi) / 2], "size": [round(float(x), 4) for x in (hi - lo)]}
    print("EXTENT", name, res[name])
reset()
out.write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
