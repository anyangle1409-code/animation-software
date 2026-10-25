"""Read-only audit: are the LM_* landmark empties in a body_v2 blend still valid for body_v2's own skin and rig?

The body_v2 blends carry R41's anatomical master and landmarks unchanged, while the body surface was rebuilt and
refitted.  For every LM_* empty:
  *_skin landmarks : distance to the nearest point of the evaluated rest skin (should be ~0 if still on the skin) and
                     whether they are inside or outside the body;
  joint centres    : (HJC, GH, EJC, WJC, KJC, AJC, SC, AC, AA, TS, AI, tibial plateau, ...) inside / outside the body
                     (ray parity along three axes, majority vote) and, where the runtime rig has a matching pivot, the
                     distance to it.
Nothing is changed or saved; the output is a JSON list sorted by severity, plus a RE-BINDING PROPOSAL (not applied):
stale skin landmarks -> the nearest skin point; the wrist centre (WJC) -> the midpoint of its two (re-bound) styloids,
the ISB wrist definition.  Other joint centres are only reported; the knee / ankle / elbow centres have their own
skin-midpoint audit (joint_centre_audit_blender.py) and the hip and shoulder centres need imaging or regression data.

With the optional joint-centre audit JSON (joint_centre_audit_blender.py on the same body), the elbow / wrist / knee /
ankle centres (EJC, WJC, KJC, AJC) are proposed at that audit's skin midpoints (ISB definitions around body_v2's own
pivots) instead; projecting R41's styloids to the nearest skin puts both on the back of body_v2's wrist, which sits
~57 mm further forward than R41's.

usage: python3.13 landmark_staleness_audit_blender.py -- <body.blend> <out.json> [joint_centre_audit.json]
"""
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

args = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = Path(args[0]), Path(args[1])
JCA = json.loads(Path(args[2]).read_text()) if len(args) > 2 else None
bpy.ops.wm.open_mainfile(filepath=str(SRC))
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]; rig = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
for kb in (body.data.shape_keys.key_blocks[1:] if body.data.shape_keys else []):
    kb.value = 0.0
dg = bpy.context.evaluated_depsgraph_get()
bvh = BVHTree.FromObject(body, dg)
MW = body.matrix_world; MWi = MW.inverted()

# runtime pivots matching a landmark (anatomical left = runtime _r)
PIVOT = {"hip_bone_{a}__HJC": "thigh_{r}", "scapula_{a}__GH": "upperarm_{r}", "humerus_{a}__EJC": "forearm_{r}",
         "radius_{a}__WJC": "hand_{r}", "femur_{a}__KJC": "shin_{r}", "tibia_{a}__AJC": "foot_{r}"}


def hits_along(p, d):
    """number of skin crossings on the ray p + t d, t > 0"""
    n, o = 0, p.copy()
    for _ in range(64):
        loc, _, _, _ = bvh.ray_cast(o, d)
        if loc is None:
            break
        n += 1; o = loc + d * 1e-5
    return n


def inside(p):
    votes = [hits_along(p, d) % 2 == 1 for d in (Vector((0, 1, 0)), Vector((1, 0, 0)), Vector((0, 0, 1)),
                                                  Vector((0, -1, 0)), Vector((-1, 0, 0)), Vector((0, 0, -1)))]
    return sum(votes) >= 4, sum(votes)


rows = []
for ob in sorted((o for o in bpy.data.objects if o.name.startswith("LM_")), key=lambda o: o.name):
    w = ob.matrix_world.translation
    pl = MWi @ w
    near, _, _, dist = bvh.find_nearest(pl)
    ins, votes = inside(pl)
    key = ob.name[3:]
    row = {"landmark": ob.name, "world_m": [round(x, 4) for x in w], "inside_body": ins, "inside_votes_of_6": votes,
           "nearest_skin_mm": round(dist * 1000, 1)}
    for pat, bone in PIVOT.items():
        for a, r in (("left", "r"), ("right", "l")):
            if key == pat.format(a=a):
                b = rig.data.bones[bone.format(r=r)]
                row["rig_pivot"] = b.name
                row["to_rig_pivot_mm"] = round(((rig.matrix_world @ b.head_local) - w).length * 1000, 1)
    if key.endswith("_skin"):
        row["kind"] = "skin"
        row["stale"] = dist > 0.004
        row["issue"] = f"{row['nearest_skin_mm']} mm {'inside' if ins else 'outside'} the skin" if row["stale"] else ""
    else:
        row["kind"] = "joint_or_bony"
        row["stale"] = not ins
        row["issue"] = f"outside the body by {row['nearest_skin_mm']} mm" if not ins else ""
    rows.append(row)
# re-binding proposal (data only)
byname = {r["landmark"]: r for r in rows}
for r in rows:
    if r["kind"] == "skin" and r["stale"]:
        ob = bpy.data.objects[r["landmark"]]
        near, _, _, _ = bvh.find_nearest(MWi @ ob.matrix_world.translation)
        r["proposed_world_m"] = [round(x, 4) for x in MW @ near]
        r["proposed_rule"] = "nearest point of the body_v2 rest skin"
for side in ("left", "right"):
    w = byname.get(f"LM_radius_{side}__WJC")
    a, b = byname.get(f"LM_humerus_{side}__styloid_radial_skin"), byname.get(f"LM_humerus_{side}__styloid_ulnar_skin")
    if w and a and b:
        pa = Vector(a.get("proposed_world_m", a["world_m"])); pb = Vector(b.get("proposed_world_m", b["world_m"]))
        m = (pa + pb) / 2
        w["proposed_world_m"] = [round(x, 4) for x in m]
        w["proposed_rule"] = "midpoint of the (re-bound) radial and ulnar styloid skin landmarks (ISB wrist centre)"
        w["proposed_inside_body"] = inside(MWi @ m)[0]
        if "rig_pivot" in w:
            w["proposed_to_rig_pivot_mm"] = round(((rig.matrix_world @ rig.data.bones[w["rig_pivot"]].head_local) - m).length * 1000, 1)
if JCA:
    joints = JCA.get("joints", JCA)
    for lm, jn in (("humerus_{a}__EJC", "elbow"), ("radius_{a}__WJC", "wrist"), ("femur_{a}__KJC", "knee"), ("tibia_{a}__AJC", "ankle")):
        for a, r_ in (("left", "r"), ("right", "l")):
            w = byname.get("LM_" + lm.format(a=a)); j = joints.get(f"{jn}_{r_}")
            if w and j:
                m = Vector(j["skin_mid_m"])
                w["proposed_world_m"] = [round(x, 4) for x in m]
                w["proposed_rule"] = f"joint_centre_audit skin midpoint ({jn}_{r_}; ISB definition)"
                w["proposed_inside_body"] = inside(MWi @ m)[0]
                if "rig_pivot" in w:
                    w["proposed_to_rig_pivot_mm"] = round(((rig.matrix_world @ rig.data.bones[w["rig_pivot"]].head_local) - m).length * 1000, 1)
rows.sort(key=lambda r: (not r["stale"], -r["nearest_skin_mm"]))
rep = {"source": SRC.name, "landmarks": len(rows), "stale": sum(r["stale"] for r in rows),
       "rule": "skin landmarks stale if > 4 mm from the skin; joint / bony landmarks stale if outside the body",
       "rows": rows}
OUT.write_text(json.dumps(rep, indent=1))
print("LMAUDIT", json.dumps({"landmarks": rep["landmarks"], "stale": rep["stale"]}), flush=True)
for r in rows:
    if r["stale"] or "to_rig_pivot_mm" in r:
        print(r["landmark"], r["kind"], r["issue"], r.get("rig_pivot", ""), r.get("to_rig_pivot_mm", ""),
              "proposed" if "proposed_world_m" in r else "", r.get("proposed_to_rig_pivot_mm", ""), r.get("proposed_inside_body", ""))
