"""First-party axial-twist helper bones: definitions shared by the authoring tool and the audits (bpy-free except drive()).

Why (docs/SKELETON_HUMAN_MOVEMENT_AND_BONE_SUFFICIENCY_POLICY.md, evidence
ORIGINAL_V1_WORK/candidates/repair_checks/skeleton_lock_r38/r38_twist_stress.json): when the forearm or upper arm rotates about
its own long axis, the flesh next to the previous joint is forced to carry the WHOLE rotation (forearm: slice radius 0.76 and
edge ratio 0.70 at 90 degrees; upper arm: edge ratio 0.28 at 90 degrees) because no bone provides the 0 % / 50 % twist stations a
real limb has. Three stations per segment fix that:

    <segment>_tw0_<side>  follows the segment's SWING only        (0 % of its axial twist)
    <segment>_tw1_<side>  follows the swing plus half the twist   (50 %)
    <segment>_<side>      the existing bone, full twist            (100 %)

Each helper is a child of the segment bone. Its local pose rotation is a pure rotation about the bone's own Y (long) axis:

    helper.local = Ry( -(1 - f) * twist ),   twist = swing-twist angle of the segment's local rotation about local Y,
                                             f = 0 (tw0) or 0.5 (tw1)

so parent_world * segment_local * helper_local = parent_world * swing * Ry(f * twist). Closed form, deterministic, no
constraints or drivers needed: a runtime computes the four angles per frame from the arm bone rotations. With zero axial twist
every helper is the identity and the skinning is bit-identical to the 63-bone rig.

Skin weights are split from the segment bone's existing weight with a partition of unity along the rest axis
(t = 0 head .. 1 tail): tw0 (1-2t)+, tw1 triangle peaking at t = 0.5, segment bone (2t-1)+ (clamped outside 0..1).
"""
from __future__ import annotations

import math

SEGMENTS = ("upperarm", "forearm")
STATIONS = (("tw0", 0.0), ("tw1", 0.5))
SIDES = ("l", "r")
REVISION = "rev2_twist_helpers"


def helper_names():
    return [f"{seg}_{st}_{s}" for seg in SEGMENTS for s in SIDES for st, _ in STATIONS]


def helper_spec():
    return [{"name": f"{seg}_{st}_{s}", "parent": f"{seg}_{s}", "twist_fraction": f, "segment": seg, "side": s}
            for seg in SEGMENTS for s in SIDES for st, f in STATIONS]


def partition(t):
    """(w_tw0, w_tw1, w_segment) for a vertex at rest-axis coordinate t. Sums to 1."""
    a0 = min(1.0, max(0.0, 1.0 - 2.0 * t))
    a1 = min(1.0, max(0.0, 1.0 - abs(2.0 * t - 1.0))) if 0.0 <= t <= 1.0 else 0.0
    a2 = min(1.0, max(0.0, 2.0 * t - 1.0))
    return a0, a1, a2


def twist_angle(q):
    """Twist (radians) of a bone-local rotation quaternion (w,x,y,z) about the local Y axis (swing-twist, Q = swing * twist)."""
    w, y = float(q[0]), float(q[2])
    ang = 2.0 * math.atan2(y, w)
    return (ang + math.pi) % (2.0 * math.pi) - math.pi


def drive(rig):
    """Set every helper pose bone from its segment bone's current local rotation (no-op on a rig without helpers)."""
    from mathutils import Matrix, Quaternion
    pose = rig.pose.bones
    for h in helper_spec():
        if h["name"] not in pose or h["parent"] not in pose:
            continue
        seg = pose[h["parent"]]
        q = seg.matrix_basis.to_quaternion()
        ang = -(1.0 - h["twist_fraction"]) * twist_angle(q)
        pose[h["name"]].matrix_basis = Quaternion((0.0, 1.0, 0.0), ang).to_matrix().to_4x4()
