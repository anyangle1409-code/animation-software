"""Read-only proof test: is the pre-close grip penetration independent of skin weights?

blender --background --factory-startup <candidate.blend> --python-exit-code 1 ^
  --python scripts/probe_original_v1_grip_weight_independence_blender.py -- <out.json>

Reuses the frozen pose definitions (executed up to the metrics marker, like the other probes) and builds the
curl_handle / pullup_bar pose exactly up to - but not including - close_on_handle. At that moment no finger or
thumb bone has been bent. If every hand-chain bone then carries the same armature-space skinning matrix
(pose x rest^-1), every weight blend of those bones maps a rest vertex to the same posed position, so no
re-weighting can change the pre-close penetration. The probe reports the largest deviation between the
skinning matrices of the hand-chain bones. Never saves the Blend; changes no pose, handle frame or gate.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import bpy
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if not args:
    raise SystemExit("output JSON path required")
out = Path(args[0])

src = Path(__file__).with_name("pose_test_original_v1_o4_candidate_blender.py").read_text(encoding="utf-8")
src = src[:src.index("# ---------------------------------------------------------------- metrics")]
tmp = tempfile.mkdtemp()
saved = sys.argv
sys.argv = ["blender", "--", tmp, ""]
ns = {"__name__": "pose_defs", "__file__": "pose_test_original_v1_o4_candidate_blender.py"}
exec(compile(src, "pose_test_defs", "exec"), ns)
sys.argv = saved

rig, body = ns["rig"], ns["body"]
upd, aim, twist_palm, place_handle = ns["upd"], ns["aim"], ns["twist_palm"], ns["place_handle"]
D, F, U, B, lat = ns["D"], ns["F"], ns["U"], ns["B"], ns["lat"]
rw = np.array(rig.matrix_world)
CHAIN = ("hand", "metacarpal_index", "metacarpal_middle", "metacarpal_ring", "metacarpal_pinky",
         "thumb_01", "thumb_02", "thumb_03", "index_01", "index_02", "index_03", "middle_01", "middle_02",
         "middle_03", "ring_01", "ring_02", "ring_03", "pinky_01", "pinky_02", "pinky_03")


def skin(name):
    pb = rig.pose.bones[name]
    return np.array(pb.matrix) @ np.linalg.inv(np.array(rig.data.bones[name].matrix_local))


def pre_close(pose, s):
    ns["reset"]()
    rig.location = (0, 0, 0)
    upd()
    ns["HANDLE"].clear()
    if pose == "curl_handle":
        aim(f"upperarm_{s}", D + F * 0.18)
        aim(f"forearm_{s}", U * 0.95 + F * 0.55 + lat(s) * -0.05)
        twist_palm(s, B + U * 0.2)
    else:
        aim(f"upperarm_{s}", lat(s))
        aim(f"upperarm_{s}", U + lat(s) * 0.45)
        aim(f"forearm_{s}", U + lat(s) * 0.35)
        twist_palm(s, F)
    place_handle(s)
    upd()
    ref = skin(f"hand_{s}")
    dev = {n: float(np.abs(skin(f"{n}_{s}") - ref).max()) for n in CHAIN}
    return dev


result = {"schema_version": 1, "candidate": Path(bpy.data.filepath).name,
          "purpose": ("max element deviation between each hand-chain bone's armature-space skinning matrix and the "
                      "hand bone's, immediately BEFORE close_on_handle (no finger/thumb bent yet)"),
          "poses": {}}
worst = 0.0
for pose in ("curl_handle", "pullup_bar"):
    result["poses"][pose] = {}
    for s in "lr":
        dev = pre_close(pose, s)
        result["poses"][pose][s] = dev
        worst = max(worst, max(dev.values()))
result["max_deviation_overall"] = worst
result["weights_cannot_change_pre_close_depth"] = bool(worst < 1e-5)
out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print("WEIGHT INDEPENDENCE max skinning-matrix deviation across the hand chain: %.3e -> %s"
      % (worst, "PROVEN weight-independent" if worst < 1e-5 else "NOT proven"))
