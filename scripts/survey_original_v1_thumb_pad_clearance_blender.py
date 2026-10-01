"""Read-only survey of the pre-close thumb/handle clearance (Phase 3C evidence; never saves the Blend).

blender --background --factory-startup <candidate.blend> --python-exit-code 1 ^
  --python scripts/survey_original_v1_thumb_pad_clearance_blender.py -- <out.json>

Builds the frozen curl_handle and pullup_bar poses up to, but not including, close_on_handle (so the frozen handle
frame from place_handle is used exactly as it is) and, for every body vertex, records the signed distance to the
handle surface (negative = inside) with all hand-chain bones carrying the same rigid transform S (verified here).
Because S is rigid and identical for every hand-chain bone, rest -> posed is  p = R x + t  and the handle frame can be
expressed in the REST coordinates of the hand: c_rest = S^-1 c_world, a_rest = R^T a_world. The output therefore
describes the clearance problem purely in rest geometry, which is what a local geometry correction acts on.
Nothing frozen is modified: poses, handle frame, thresholds and rig are read only.
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
saved = sys.argv
sys.argv = ["blender", "--", tempfile.mkdtemp(), ""]
ns = {"__name__": "pose_defs", "__file__": "pose_test_original_v1_o4_candidate_blender.py"}
exec(compile(src, "pose_test_defs", "exec"), ns)
sys.argv = saved

rig, body = ns["rig"], ns["body"]
upd, aim, twist_palm, place_handle = ns["upd"], ns["aim"], ns["twist_palm"], ns["place_handle"]
D, F, U, B, lat = ns["D"], ns["F"], ns["U"], ns["B"], ns["lat"]
mask = body.modifiers.get("HGPT_DRESSED_MASK")
if mask is not None:
    mask.show_viewport = False
    mask.show_render = False
upd()
rw = np.array(rig.matrix_world)
bw = np.array(body.matrix_world)
names = json.loads(bpy.context.scene["hgpt_region_names"])
region = np.array([d.value for d in body.data.attributes["hgpt_region"].data])
rest = np.array([v.co[:] for v in body.data.vertices])
CHAIN = ("hand", "metacarpal_index", "metacarpal_middle", "metacarpal_ring", "metacarpal_pinky", "thumb_01", "thumb_02",
         "thumb_03", "index_01", "index_02", "index_03", "middle_01", "middle_02", "middle_03", "ring_01", "ring_02",
         "ring_03", "pinky_01", "pinky_02", "pinky_03")


def skin(name):
    pb = rig.pose.bones[name]
    return rw @ np.array(pb.matrix) @ np.linalg.inv(np.array(rig.data.bones[name].matrix_local)) @ np.linalg.inv(rw) @ bw


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
    S = skin(f"hand_{s}")
    dev = max(float(np.abs(skin(f"{n}_{s}") - S).max()) for n in CHAIN)
    Rm, t = S[:3, :3], S[:3, 3]
    if abs(np.linalg.det(Rm) - 1.0) > 1e-5 or np.abs(Rm @ Rm.T - np.eye(3)).max() > 1e-5:
        raise SystemExit("hand skinning transform is not a rigid rotation")
    P = rest @ Rm.T + t                                   # posed position of every vertex, all hand-chain bones identical
    c_w, a_w = ns["HANDLE"][s]
    c_w, a_w = np.array(c_w), np.array(a_w)
    c_r, a_r = Rm.T @ (c_w - t), Rm.T @ a_w               # handle frame in REST coordinates of the hand
    d = ns["handle_distance"](P, s)                       # signed distance in metres, negative = inside the handle
    return {"max_chain_matrix_deviation": dev, "handle_centre_rest": c_r.tolist(), "handle_axis_rest": a_r.tolist(),
            "handle_radius_m": float(ns["HANDLE_RADIUS"]), "signed_distance_m": d}


result = {"schema_version": 1, "candidate": Path(bpy.data.filepath).name,
          "purpose": "pre-close signed distance (m) of every body vertex to the frozen handle, and the handle frame in rest coordinates",
          "region_names": names, "poses": {}}
dist = {}
for pose in ("curl_handle", "pullup_bar"):
    result["poses"][pose] = {}
    for s in "lr":
        r = pre_close(pose, s)
        dist[(pose, s)] = r.pop("signed_distance_m")
        result["poses"][pose][s] = r
thumb = np.isin(region, [names.index("thumb")])
summary = {}
for s in "lr":
    # per side: a vertex belongs to this side's hand if its x has the side's sign; take the signed distance from that
    # side's handle only (the other side's handle is far away)
    side = (rest[:, 0] < 0) if s == "l" else (rest[:, 0] > 0)
    for pose in ("curl_handle", "pullup_bar"):
        d = dist[(pose, s)]
        inside = np.nonzero(side & (d < 0) & thumb)[0]
        summary[f"{pose}/{s}"] = {"vertices_inside": [int(i) for i in inside],
                                  "max_penetration_mm": float(-d[inside].min() * 1000) if len(inside) else 0.0,
                                  "inside_regions": sorted({names[region[i]] for i in np.nonzero(side & (d < 0))[0]})}
        result["poses"][pose][s]["distance_to_handle_mm_thumb_region"] = {int(i): round(float(d[i]) * 1000, 4)
                                                                        for i in np.nonzero(side & thumb & (d < 0.02))[0]}
result["summary"] = summary
result["max_chain_matrix_deviation_overall"] = max(r["max_chain_matrix_deviation"]
                                                   for p in result["poses"].values() for r in p.values())
out.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
print("THUMB SURVEY", json.dumps({k: (len(v["vertices_inside"]), round(v["max_penetration_mm"], 3), v["inside_regions"])
                                  for k, v in summary.items()}), "chain deviation %.2e" % result["max_chain_matrix_deviation_overall"])
