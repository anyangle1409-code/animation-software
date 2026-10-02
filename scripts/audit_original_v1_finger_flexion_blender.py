"""Read-only finger-flexion audit about a FIXED, hand-anchored flexion axis (never saves the .blend).

blender --background --factory-startup <candidate.blend> --python-exit-code 1 ^
  --python scripts/audit_original_v1_finger_flexion_blender.py -- <out.json> [pose,pose,...]

Why this exists: scripts/audit_original_v1_skeleton_motion_blender.py measures each finger joint about an axis recomputed
from that segment's own (already curled) direction (d x palm_normal). That axis flips sign once the cumulative curl passes
90 degrees, so a reversed distal bend still reads as a positive bend and the reversal flag never fires. A finger is a set
of parallel hinges: this tool takes the flexion axis ONCE from the neutral rest pose (finger direction x palm normal),
stores it in the hand bone's local frame, and measures every joint about that same axis in every pose.

Positive angle = flexion toward the palm. Per finger it reports metacarpal->proximal (MCP), proximal->middle (PIP),
middle->distal (DIP) and the cumulative direction angle. Anatomical envelope used for flags (reference-only; see
docs/EXTERNAL_HUMAN_MOVEMENT_REFERENCE_POLICY.md): each joint flexes in the same sense (>= -2 deg), MCP <= ~100,
PIP <= ~110, DIP <= ~90.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if not args:
    raise SystemExit("Usage: ... -- <out.json> [pose,pose,...]")
OUT = Path(args[0]).resolve()
ONLY = set(args[1].split(",")) if len(args) > 1 and args[1] else None

pose_script = Path(__file__).with_name("pose_test_original_v1_o4_candidate_blender.py")
src = pose_script.read_text(encoding="utf-8")
src_defs = src[:src.index("# ---------------------------------------------------------------- metrics")]
saved_argv = sys.argv
sys.argv = ["blender", "--", tempfile.mkdtemp(), ""]
ns = {"__name__": "pose_defs", "__file__": pose_script.name}
exec(compile(src_defs, "pose_test_defs", "exec"), ns)
sys.argv = saved_argv
rig, POSES, pb, reset, upd, palm_normal = ns["rig"], ns["POSES"], ns["pb"], ns["reset"], ns["upd"], ns["palm_normal"]
_mask = ns["body"].modifiers.get("HGPT_DRESSED_MASK")
if _mask is not None:
    _mask.show_viewport = False
    _mask.show_render = False
FINGERS = ("index", "middle", "ring", "pinky")


def dirn(name):
    p = pb(name)
    d = p.tail - p.head
    return d.normalized()


def rest_axes():
    """Per side/finger flexion axis in the hand bone's local frame, taken from the neutral pose."""
    reset()
    out = {}
    for s in "lr":
        hand_inv = pb(f"hand_{s}").matrix.to_3x3().inverted()
        n = palm_normal(s)
        for f in FINGERS:
            ax = dirn(f"{f}_01_{s}").cross(n).normalized()
            out[(s, f)] = hand_inv @ ax
    return out


AXES = rest_axes()


def signed(a, b, axis):
    a, b = a.normalized(), b.normalized()
    return math.degrees(math.atan2(axis.dot(a.cross(b)), a.dot(b)))


def finger(s, f):
    axis = (pb(f"hand_{s}").matrix.to_3x3() @ AXES[(s, f)]).normalized()
    chain = [dirn(f"metacarpal_{f}_{s}"), dirn(f"{f}_01_{s}"), dirn(f"{f}_02_{s}"), dirn(f"{f}_03_{s}")]
    mcp, pip, dip = (signed(chain[i], chain[i + 1], axis) for i in range(3))
    cum = [signed(chain[0], chain[i], axis) for i in (1, 2, 3)]
    flags = []
    if min(mcp, pip, dip) < -2.0:
        flags.append("reverse_bend")
    if mcp > 100 or pip > 110 or dip > 90:
        flags.append("beyond_envelope")
    return {"mcp_deg": round(mcp, 3), "pip_deg": round(pip, 3), "dip_deg": round(dip, 3),
            "cumulative_deg": [round(c, 3) for c in cum], "flags": flags}


result = {"schema_version": 1, "generated_utc": datetime.now(timezone.utc).isoformat(),
          "purpose": "fixed-axis finger flexion audit (reversal-proof); read-only",
          "source_candidate": Path(bpy.data.filepath).name,
          "source_candidate_sha256": hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),
          "pose_definition_script_sha256": hashlib.sha256(pose_script.read_bytes()).hexdigest(),
          "positive_means": "flexion toward the palm about the neutral-rest flexion axis", "poses": [], "flagged": []}
for name, fn in POSES.items():
    if ONLY and name not in ONLY:
        continue
    reset()
    ns["rig"].location = (0, 0, 0)
    fn()
    upd()
    rec = {"pose": name, "hands": {}}
    for s in "lr":
        rec["hands"][s] = {f: finger(s, f) for f in FINGERS}
        for f, r in rec["hands"][s].items():
            for fl in r["flags"]:
                result["flagged"].append({"pose": name, "side": s, "finger": f, "flag": fl, **{k: r[k] for k in ("mcp_deg", "pip_deg", "dip_deg")}})
    result["poses"].append(rec)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print("FINGER FLEXION AUDIT", OUT, "poses", len(result["poses"]), "flags", len(result["flagged"]))
