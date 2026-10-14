"""Runtime drives of the ORIGINAL_v1 consolidated review candidate R1 (bpy).  Call drive(rig, body) after posing.

The R1 blend carries corrections that the 67-joint production contract cannot drive by itself:
  * W3 option A: `deltoid_helper_<s>` (69 deforming joints once install_helpers() has run; the blend stores the helper
    vertex groups and reference vectors, not the bones).  Each helper takes FRACTION of the upper arm's rotation
    relative to the scapula, on the axis-angle branch closest to the per-side reference vector stored on the rig as
    `hgpt_w3a_ref_<s>` (the 120 deg coupled pose): stateless, identity at rest.
  * K1: shape keys `HGPT_K1_KNEE_<s>_<deg>` / `HGPT_K1_ELBOW_<s>_<deg>`, piecewise-linear hats on the measured hinge
    angle (0 at <= 60 deg, clamped above the last key).
Review-only: every one of these is a runtime-contract change that needs owner + Lane G agreement (PR #26).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy
from mathutils import Quaternion, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_original_knee_contact_corrective_blender as k1  # noqa: E402

FRACTION = 0.5


def _rel_quat(rig, child, parent):
    pb, pp = rig.pose.bones[child], rig.pose.bones[parent]
    b, bp = rig.data.bones[child], rig.data.bones[parent]
    rest = bp.matrix_local.inverted() @ b.matrix_local
    return (rest.inverted() @ (pp.matrix.inverted() @ pb.matrix)).to_quaternion()


HELPER_LENGTH = 0.4


def install_helpers(rig):
    """Recreate deltoid_helper_l/r (69 joints) in memory: the upper arm's rest frame, 40 % length, parented like the upper
    arm; the R1 blend stores their vertex groups, weights and reference vectors but not the bones, so the saved file stays
    a 67-bone rig that the shared bridge guard accepts.  Call after any guarded scene setup, before posing."""
    if "deltoid_helper_l" in rig.data.bones:
        return
    view = bpy.context.view_layer
    for o in view.objects:
        o.select_set(False)
    view.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    for s in ("l", "r"):
        up = rig.data.edit_bones[f"upperarm_{s}"]
        h = rig.data.edit_bones.new(f"deltoid_helper_{s}")
        h.head = up.head.copy()
        h.tail = up.head + (up.tail - up.head) * HELPER_LENGTH
        h.roll = up.roll
        h.parent = up.parent
        h.use_connect = False
        h.use_deform = True
    bpy.ops.object.mode_set(mode="OBJECT")
    view.update()


def drive_helpers(rig):
    if "deltoid_helper_l" not in rig.pose.bones:
        return
    bpy.context.view_layer.update()
    for s in ("l", "r"):
        q = _rel_quat(rig, f"upperarm_{s}", f"scapula_{s}")
        if q.w < 0:
            q.negate()
        theta = q.angle
        n = q.axis if theta > 1e-9 else Vector((1.0, 0.0, 0.0))
        ref = Vector(rig[f"hgpt_w3a_ref_{s}"])
        v = min((n * theta, n * (theta - 2 * math.pi)), key=lambda c: (c - ref).length)
        h = rig.pose.bones[f"deltoid_helper_{s}"]
        h.rotation_mode = "QUATERNION"
        ang = v.length * FRACTION
        h.rotation_quaternion = Quaternion(v.normalized(), ang) if ang > 1e-12 else Quaternion()
    bpy.context.view_layer.update()


def drive_k1(rig, body):
    keys = body.data.shape_keys.key_blocks
    for hinge in ("knee", "elbow"):
        prefix = k1.HINGES[hinge]["prefix"]
        degs = sorted({int(kb.name.rsplit("_", 1)[1]) for kb in keys if kb.name.startswith(prefix)})
        if not degs:
            continue
        for s in ("l", "r"):
            for deg, v in k1.activations(k1.hinge_angle_deg(rig, hinge, s), tuple(degs)).items():
                keys[f"{prefix}{s}_{deg}"].value = v
    bpy.context.view_layer.update()


def drive(rig, body):
    install_helpers(rig)
    drive_helpers(rig)
    drive_k1(rig, body)
