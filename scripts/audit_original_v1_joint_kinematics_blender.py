"""Read-only joint kinematics + continuous-motion audit for the skeleton-motion lock (never saves the .blend).

blender --background --factory-startup <candidate.blend> --python-exit-code 1 ^
  --python scripts/audit_original_v1_joint_kinematics_blender.py -- <out.json> [pose,pose,...] [f1,f2,...]

For every pose of the frozen stress-pose set the final pose is built exactly as the pose script builds it, then the pose is
re-played CONTINUOUSLY: every pose bone's local rotation is slerped from the rest pose (fraction 0) to the final pose
(fraction 1) at the requested fractions (default 0,0.25,0.5,0.75,1; add finer ones such as 0.125,... if a problem is suspected).
At each sample every joint is decomposed into anatomical components:

  flex_deg   swing component toward the anatomical "flexion" direction (rotation-vector component; sign convention below)
  abd_deg    swing component toward the anatomical "abduction / lateral" direction
  twist_deg  axial rotation about the bone's rest direction (right-hand rule about the distal direction)

relative to the parent bone (the parent's own motion is removed), expressed in the neutral-rest anatomical frame. The rest
skeleton has every long bone aligned with a world axis (A-pose arms hang along -Z, palms face the body, foot points forward),
so the anatomical frame is the world frame: F = (0,-1,0) character forward, U = (0,0,1), lateral(side) = (+-1,0,0).

Conventions (positive = ...): flex = rotation toward flexion (shoulder/hip: distal end forward; elbow: forearm forward;
knee: shin BACKWARD; neck/head/spine: forward; ankle: toes up (dorsiflexion); toe: toes up; wrist/fingers: toward the palm).
abd = away from the midline (limbs) or toward the character's left (spine/neck). The report also lists, per joint and pose,
monotonicity of the sampled path (sign flips, largest step between consecutive samples) so endpoint-only hiding is impossible.
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
from mathutils import Matrix, Quaternion, Vector

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if not args:
    raise SystemExit("Usage: ... -- <out.json> [pose,pose,...] [f1,f2,...]")
OUT = Path(args[0]).resolve()
ONLY = set(args[1].split(",")) if len(args) > 1 and args[1] else None
FRACS = [float(x) for x in args[2].split(",")] if len(args) > 2 and args[2] else [0.0, 0.25, 0.5, 0.75, 1.0]

pose_script = Path(__file__).with_name("pose_test_original_v1_o4_candidate_blender.py")
src = pose_script.read_text(encoding="utf-8")
src_defs = src[:src.index("# ---------------------------------------------------------------- metrics")]
saved_argv = sys.argv
sys.argv = ["blender", "--", tempfile.mkdtemp(), ""]
ns = {"__name__": "pose_defs", "__file__": pose_script.name}
exec(compile(src_defs, "pose_test_defs", "exec"), ns)
sys.argv = saved_argv
rig, POSES, reset, upd = ns["rig"], ns["POSES"], ns["reset"], ns["upd"]
_mask = ns["body"].modifiers.get("HGPT_DRESSED_MASK")
if _mask is not None:
    _mask.show_viewport = False
    _mask.show_render = False

F = Vector((0, -1, 0))
U = Vector((0, 0, 1))
X = Vector((1, 0, 0))


def side_sign(name):
    return -1.0 if name.endswith("_l") else 1.0      # character's left is -X in this rig


def anatomical(bone):
    """(flex_dir, abd_dir) world vectors for the neutral rest frame, or None for a bone that is only reported generically."""
    s = side_sign(bone)
    lat = X * s                                       # away from the midline for this side
    med = -lat
    n = bone[:-2] if bone.endswith(("_l", "_r")) else bone
    if n in ("upperarm", "thigh"):
        return F, lat
    if n == "forearm":
        return F, lat
    if n == "shin":
        return -F, lat
    if n == "hand":
        return med, F * 1.0                           # flexion toward the palm (medial at rest); radial deviation = forward (thumb side)
    if n.startswith("metacarpal") or n.endswith(("_01", "_02", "_03")) and n.split("_")[0] in ("index", "middle", "ring", "pinky"):
        return med, F                                 # toward the palm; abduction = spread toward the thumb side
    if n.startswith("thumb"):
        return med, F
    if n in ("foot", "toe"):
        return U, lat
    if n in ("neck", "head", "spine_01", "spine_02", "spine_03", "pelvis"):
        return F, -X                                  # lateral bend toward the character's left (-X)
    if n in ("clavicle", "scapula"):
        return U, F                                   # flex = elevation, abd = protraction (forward)
    return None


def rot3(m):
    return m.to_3x3()


REST3 = {b.name: rot3(b.matrix_local) for b in rig.data.bones}
REST_DIR = {b.name: (Vector(b.tail_local) - Vector(b.head_local)).normalized() for b in rig.data.bones}


def world_q(name):
    """World-axes rotation of the bone relative to its own rest orientation."""
    return (rot3(rig.pose.bones[name].matrix) @ REST3[name].inverted()).to_quaternion()


def joint(name):
    p = rig.pose.bones[name]
    q = world_q(name)
    if p.parent is not None:
        q = world_q(p.parent.name).inverted() @ q
    return q


def swing_twist(q, axis):
    ax = axis.normalized()
    v = Vector((q.x, q.y, q.z))
    proj = ax * v.dot(ax)
    tw = Quaternion((q.w, proj.x, proj.y, proj.z))
    if tw.magnitude < 1e-12:
        tw = Quaternion((1, 0, 0, 0))
    tw.normalize()
    sw = q @ tw.inverted()
    return sw, tw


def deg(x):
    return math.degrees(x)


def joint_angles(name):
    q = joint(name)
    t0 = REST_DIR[name]
    sw, tw = swing_twist(q, t0)
    d = sw @ t0
    ang = anatomical(name)
    out = {"swing_total_deg": round(deg(d.angle(t0)), 4)}
    ti = 2.0 * math.atan2(Vector((tw.x, tw.y, tw.z)).dot(t0), tw.w)
    ti = (ti + math.pi) % (2 * math.pi) - math.pi
    out["twist_deg"] = round(deg(ti), 4)
    if ang is not None:
        # rotation-vector components of the swing: a rotation about unit axis a by angle A moves the distal end toward a x t0,
        # so the flexion component is A * a.(t0 x flex_dir). Unlike atan2 of the end direction this stays correct past 90 degrees.
        fl, ab = ang
        axis, angle = sw.to_axis_angle()
        if angle > 1e-9:
            out["flex_deg"] = round(deg(angle * axis.dot(t0.cross(fl))), 4)
            out["abd_deg"] = round(deg(angle * axis.dot(t0.cross(ab))), 4)
        else:
            out["flex_deg"] = out["abd_deg"] = 0.0
    return out


BONES = [b.name for b in rig.data.bones if b.name != "root"]


def final_local():
    return {p.name: (p.matrix_basis.to_quaternion(), p.matrix_basis.to_translation()) for p in rig.pose.bones}


def apply_fraction(final, f):
    """Sample the pose at fraction f of the way from rest. Each joint rotation is split into swing and twist about the bone's own
    axis (Q = swing * twist) and the two parts are interpolated SEPARATELY (swing by slerp, twist by angle). A single slerp of the
    whole quaternion mixes flexion with twist along the path and shows a transient sideways bend that no hinge joint has (it appeared
    as a 20-44 degree elbow 'abduction' mid-path in the supinated curl); this is the interpolation a runtime solver should use."""
    for p in rig.pose.bones:
        q, t = final[p.name]
        sw, tw = swing_twist(q, Vector((0, 1, 0)))
        ang = 2.0 * math.atan2(tw.y, tw.w)
        ang = (ang + math.pi) % (2.0 * math.pi) - math.pi
        qf = Quaternion((1, 0, 0, 0)).slerp(sw, f) @ Quaternion((0.0, 1.0, 0.0), f * ang)
        p.matrix_basis = Matrix.Translation(t * f) @ qf.to_matrix().to_4x4()
    upd()


source = Path(bpy.data.filepath)
result = {"schema_version": 1, "generated_utc": datetime.now(timezone.utc).isoformat(),
          "purpose": "joint kinematics and continuous-motion audit (read-only)",
          "source_candidate": source.name, "source_candidate_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
          "pose_definition_script_sha256": hashlib.sha256(pose_script.read_bytes()).hexdigest(),
          "fractions": FRACS, "poses": [], "path_flags": []}
for pose_name, fn in POSES.items():
    if ONLY and pose_name not in ONLY:
        continue
    reset()
    rig.location = (0, 0, 0)
    ns["HANDLE"].clear()
    fn()
    upd()
    final = final_local()
    samples = []
    for f in FRACS:
        apply_fraction(final, f)
        samples.append({"fraction": f, "joints": {b: joint_angles(b) for b in BONES}})
    result["poses"].append({"pose": pose_name, "samples": samples})
    # path checks: per joint component, sign flips (> 5 deg amplitude) and the largest consecutive step
    for b in BONES:
        for comp in ("flex_deg", "abd_deg", "twist_deg"):
            series = [s["joints"][b].get(comp) for s in samples]
            if any(v is None for v in series):
                continue
            peak = max(abs(v) for v in series)
            if peak < 5.0:
                continue
            signs = [1 if v > 2.0 else -1 if v < -2.0 else 0 for v in series]
            nz = [x for x in signs if x]
            flips = sum(1 for a, c in zip(nz, nz[1:]) if a != c)
            step = max(abs(a - c) for a, c in zip(series, series[1:]))
            if flips or step > 120:
                result["path_flags"].append({"pose": pose_name, "bone": b, "component": comp, "sign_flips": flips,
                                             "max_step_deg": round(step, 2), "series": series})
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
print("JOINT KINEMATICS", OUT, "poses", len(result["poses"]), "path_flags", len(result["path_flags"]))
