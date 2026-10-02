"""Read-only floor-contact audit for support poses (never saves the .blend).

blender --background --factory-startup <candidate.blend> --python-exit-code 1 ^
  --python scripts/audit_original_v1_floor_contact_blender.py -- <out.json> [pose,pose,...]

For each pose (default: pushup_bottom, lunge, squat_bottom) the pose is built exactly as the pose script builds it (including its
grounding step), the skinned mesh is evaluated and every vertex within CONTACT_MM of the floor (z = 0) is grouped by body region and by
the dominant deform bone. Reports the contact patch per region, the palm-normal angle to the floor and the hand/foot bone angles, so a
'loaded palm planted flat vs side-edge loading' or 'forefoot/toe-pad support' claim rests on numbers.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import tempfile
from collections import Counter
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if not args:
    raise SystemExit("Usage: ... -- <out.json> [pose,...]")
OUT = Path(args[0]).resolve()
ONLY = args[1].split(",") if len(args) > 1 and args[1] else ["pushup_bottom", "lunge", "squat_bottom"]
CONTACT_MM = 6.0

pose_script = Path(__file__).with_name("pose_test_original_v1_o4_candidate_blender.py")
src = pose_script.read_text(encoding="utf-8")
saved = sys.argv
sys.argv = ["blender", "--", tempfile.mkdtemp(), ""]
ns = {"__name__": "pose_defs", "__file__": pose_script.name}
exec(compile(src[:src.index("# ---------------------------------------------------------------- metrics")], "pose_test_defs", "exec"), ns)
sys.argv = saved
rig, body, POSES, reset, upd = ns["rig"], ns["body"], ns["POSES"], ns["reset"], ns["upd"]
mask = body.modifiers.get("HGPT_DRESSED_MASK")
if mask is not None:
    mask.show_viewport = False
    mask.show_render = False
names = json.loads(bpy.context.scene["hgpt_region_names"])
region = np.array([d.value for d in body.data.attributes["hgpt_region"].data])
group_names = {vg.index: vg.name for vg in body.vertex_groups}
bone_names = {b.name for b in rig.data.bones}
dom = []
for v in body.data.vertices:
    gs = [(group_names[g.group], g.weight) for g in v.groups if group_names[g.group] in bone_names]
    dom.append(max(gs, key=lambda x: x[1])[0] if gs else "none")
dom = np.array(dom)
ids = list(range(len(body.data.vertices)))
result = {"schema_version": 1, "source_candidate": Path(bpy.data.filepath).name,
          "source_candidate_sha256": hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),
          "pose_definition_script_sha256": hashlib.sha256(pose_script.read_bytes()).hexdigest(), "contact_mm": CONTACT_MM, "poses": {}}
for pose in ONLY:
    reset()
    rig.location = (0, 0, 0)
    ns["HANDLE"].clear()
    POSES[pose]()
    upd()
    P = ns["evaluated_positions"](ids)
    z = P[:, 2]
    near = z < z.min() + CONTACT_MM / 1000.0
    rec = {"min_z_m": round(float(z.min()), 5), "contact_vertices": int(near.sum()), "by_region": dict(Counter(names[r] for r in region[near])),
           "by_dominant_bone": dict(Counter(dom[near].tolist()).most_common(12))}
    rec["min_z_by_region_m"] = {names[r]: round(float(z[region == r].min()), 5) for r in sorted(set(region.tolist()))}
    for side in "lr":
        sel = near & (P[:, 0] * (-1 if side == "l" else 1) > 0)
        if sel.any():
            rec[f"patch_{side}"] = {"x_range_m": [round(float(P[sel, 0].min()), 4), round(float(P[sel, 0].max()), 4)],
                                    "y_range_m": [round(float(P[sel, 1].min()), 4), round(float(P[sel, 1].max()), 4)], "vertices": int(sel.sum())}
    for side in "lr":
        pn = ns["palm_normal"](side)
        rec[f"palm_normal_{side}"] = [round(float(x), 4) for x in pn]
        rec[f"palm_normal_to_down_deg_{side}"] = round(math.degrees(pn.angle(Vector((0, 0, -1)))), 2)
        rec[f"hand_dir_{side}"] = [round(float(x), 4) for x in ns["bdir"](f"hand_{side}")]
        rec[f"toe_dir_{side}"] = [round(float(x), 4) for x in ns["bdir"](f"toe_{side}")]
    result["poses"][pose] = rec
    print("FLOOR", pose, rec["contact_vertices"], rec["by_region"])
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
