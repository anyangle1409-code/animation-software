"""Read-only ORIGINAL-v1 grip penetration probe.

Blender invocation:
  blender --background --factory-startup <candidate.blend> --python-exit-code 1 ^
    --python scripts/probe_original_v1_grip_penetration_blender.py -- <out.json>

The current evidence reports the same grip penetration in curl_handle and
pullup_bar. This probe records the deepest vertices before and after finger
closing, their rest positions and weights, plus the generated handle frames.
It never changes the candidate or the acceptance gate.
"""
from __future__ import annotations

import hashlib
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
saved_argv = sys.argv
sys.argv = ["blender", "--", tmp, ""]
ns = {"__name__": "pose_defs", "__file__": "pose_test_original_v1_o4_candidate_blender.py"}
exec(compile(src, "pose_test_defs", "exec"), ns)
sys.argv = saved_argv

rig = ns["rig"]
body = ns["body"]
region_names = ns["region_names"]
vreg = ns["vreg"]
owners = ns["bone_vertex_sets"]()
ns["OWNERS"] = owners

group_name = {g.index: g.name for g in body.vertex_groups}
deform = {b.name for b in rig.data.bones if b.use_deform}


def top_weights(vertex_id):
    v = body.data.vertices[vertex_id]
    vals = []
    for g in v.groups:
        name = group_name[g.group]
        if name in deform and g.weight > 1e-8:
            vals.append((name, float(g.weight)))
    vals.sort(key=lambda x: -x[1])
    return [{"bone": n, "weight": round(w, 6)} for n, w in vals[:4]]


def finger_ids(side):
    return sorted({
        i
        for f in ("index", "middle", "ring", "pinky", "thumb")
        for k in (1, 2, 3)
        for i in owners.get(f + "_0" + str(k) + "_" + side, [])
    })


def sample(side):
    ids = finger_ids(side)
    P = ns["evaluated_positions"](ids)
    d = ns["handle_distance"](P, side)
    order = np.argsort(d)
    deepest = []
    for j in order[:12]:
        vid = int(ids[int(j)])
        deepest.append({
            "vertex": vid,
            "signed_distance_mm": round(float(d[int(j)]) * 1000.0, 4),
            "penetration_mm": round(float(max(0.0, -d[int(j)])) * 1000.0, 4),
            "region": region_names[int(vreg[vid])],
            "rest_position": [round(float(x), 6) for x in body.data.vertices[vid].co],
            "top_weights": top_weights(vid),
        })
    return {
        "max_penetration_mm": round(float(max(0.0, -d.min())) * 1000.0, 4),
        "inside_vertices": int((d < 0).sum()),
        "contact_vertices_within_2mm": int((np.abs(d) < 0.002).sum()),
        "finger_vertices": len(ids),
        "deepest": deepest,
    }


def setup_pose(name):
    ns["reset"]()
    rig.location = (0, 0, 0)
    rig.rotation_euler = (0, 0, 0)
    ns["upd"]()
    ns["HANDLE"].clear()
    if name == "curl_handle":
        for s in "lr":
            ns["aim"]("upperarm_" + s, ns["D"] + ns["F"] * 0.18)
            ns["aim"]("forearm_" + s, ns["U"] * 0.95 + ns["F"] * 0.55 + ns["lat"](s) * -0.05)
            ns["twist_palm"](s, ns["B"] + ns["U"] * 0.2)
            ns["place_handle"](s)
    elif name == "pullup_bar":
        for s in "lr":
            ns["aim"]("upperarm_" + s, ns["lat"](s))
            ns["aim"]("upperarm_" + s, ns["U"] + ns["lat"](s) * 0.45)
            ns["aim"]("forearm_" + s, ns["U"] + ns["lat"](s) * 0.35)
            ns["twist_palm"](s, ns["F"])
            ns["place_handle"](s)
    else:
        raise ValueError(name)


result = {
    "schema_version": 1,
    "candidate": Path(bpy.data.filepath).name,
    "source_candidate_sha256": hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),
    "pose_script_sha256": hashlib.sha256(Path(__file__).with_name("pose_test_original_v1_o4_candidate_blender.py").read_bytes()).hexdigest(),
    "purpose": "read-only evidence for thumb/finger versus frozen handle-grip pose",
    "acceptance_gate_mm": 2.0,
    "poses": {},
}

for pose_name in ("curl_handle", "pullup_bar"):
    setup_pose(pose_name)
    entry = {"pre_close": {}, "post_close": {}, "handle": {}}
    for s in "lr":
        c, a = ns["HANDLE"][s]
        entry["handle"][s] = {
            "centre": [round(float(x), 6) for x in c],
            "axis": [round(float(x), 6) for x in a],
            "radius_m": ns["HANDLE_RADIUS"],
        }
        entry["pre_close"][s] = sample(s)
    for s in "lr":
        ns["close_on_handle"](s)
        entry["post_close"][s] = sample(s)
    result["poses"][pose_name] = entry

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print("GRIP PROBE", out)
for pose_name, entry in result["poses"].items():
    for s in "lr":
        pre = entry["pre_close"][s]["max_penetration_mm"]
        post = entry["post_close"][s]["max_penetration_mm"]
        print(pose_name, s, "penetration pre/post mm", pre, post)
