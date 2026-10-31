"""CANDIDATE, not adopted (owner decision: it changes the runtime contract and the bind): upper-arm twist bones and the
swing / twist split that drives them.  Everything here is in memory; nothing is saved to a blend.

Why: no shape key or helper is indexed by humeral axial rotation, and linear blend skinning twists the upper arm's skin
as one piece about the shoulder blend zone.  On AX6, band external rotation (arms at the sides, elbows 90) breaks the
shoulder from about 19 deg (864 self-intersections at 60 deg); the r57 helpers (deltoid, cap, armpit, muscle lines) also
take the twist with the swing.  See the trajectories doc's G1 / G2 sections.

What:
  * install(): one deform bone per side, upperarm_tw_<s>, a child of the upper arm on the same line.  Each upper-arm
    vertex's weight w is split: w * f stays on the upper arm, w * (1 - f) goes to the twist bone, f a smoothstep of the
    position along the arm, 0 at the shoulder to 1 at END (85 %) of the upper arm - so the twist is complete before the
    elbow crease (the forearm turns fully with the humerus).
  * drive(): the twist part of each upper arm's pose rotation (swing / twist split about its own long axis) OUTSIDE the
    band the authored movements already use: from -DEADBAND to the press path's own twist at this elevation (weighted
    out towards forward raises, which carry none) + DEADBAND, with a C1 ramp, exactly zero inside.  The twist bone
    counter-rotates by it, so the shoulder-end skin follows the swing alone; the r57 helpers are driven with it taken
    off the humerus.  Every authored path (press, raises, curl, squat, deadlift, lunge, pulldown) gives zero, so their
    keys stay valid; excess twist (external rotation at the side, an overhead extension's forearms-back turn) is
    spread down the arm.
"""
from __future__ import annotations

import math

import bpy
from mathutils import Matrix

END, START, POWER, SHAPE = 0.85, 0.0, 1.0, "smooth"
DEADBAND_DEG, RAMP_DEG = 5.0, 2.0
# the press path's own upper-arm twist (swing / twist split; AX6, ISB girdle frame, candidate press girdle), deg, keyed
# by the MEASURED humerothoracic elevation (drives.elevation_deg; the press's target 160 measures 153.4); the pulldown,
# which follows the press path with other elbow angles, measures the same.  + is external rotation on l, - on r.
PRESS_TWIST_M = ((12.27, 0.81), (22.76, 2.81), (47.57, 10.83), (72.75, 21.3), (84.23, 25.91), (95.09, 29.74),
                 (118.96, 34.87), (142.7, 32.91), (153.35, 28.66))
# the press's measured plane factor (r121_drives.plane_factor) is 0.04-0.27, close to a sideways raise's 0, so the band
# is weighted out only towards forward raises (plane factor 0.3 -> 0.6)
PF_FULL, PF_NONE = 0.3, 0.6
SIDES = ("l", "r")
SIGN = {"l": 1.0, "r": -1.0}


def install(rig, body, end=END, start=START, power=POWER, shape=SHAPE):
    """add upperarm_tw_<s> and split the upper-arm weights (in memory; no-op if already installed)"""
    if "upperarm_tw_l" in rig.data.bones:
        return
    view = bpy.context.view_layer
    view.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    for s in SIDES:
        up = rig.data.edit_bones[f"upperarm_{s}"]; eb = rig.data.edit_bones.new(f"upperarm_tw_{s}")
        eb.head, eb.tail, eb.roll = up.head.copy(), up.tail.copy(), up.roll
        eb.parent = up; eb.use_connect = False; eb.use_deform = True
    bpy.ops.object.mode_set(mode="OBJECT")
    MWr, MWb = rig.matrix_world, body.matrix_world
    for s in SIDES:
        b = rig.data.bones[f"upperarm_{s}"]; h = MWr @ b.head_local; t = MWr @ b.tail_local
        L = (t - h).length; ax = (t - h) / L
        src = body.vertex_groups[f"upperarm_{s}"]; dst = body.vertex_groups.new(name=f"upperarm_tw_{s}")
        for v in body.data.vertices:
            for g in v.groups:
                if g.group == src.index and g.weight > 0.0:
                    f = min(1.0, max(0.0, ((MWb @ v.co - h).dot(ax) / L - start) / (end - start))) ** power
                    if shape == "smooth":
                        f = f * f * (3.0 - 2.0 * f)
                    w = g.weight
                    src.add([v.index], w * f, "REPLACE"); dst.add([v.index], w * (1.0 - f), "REPLACE")
    view.update()


def pose_twist(rig, s):
    """the twist part (rad) of the upper arm's pose rotation about its own long axis (local Y): q = swing * twist"""
    q = rig.pose.bones[f"upperarm_{s}"].matrix_basis.to_quaternion()
    t = 2.0 * math.atan2(q.y, q.w)
    return (t + math.pi) % (2.0 * math.pi) - math.pi


def press_twist_band(elevation_deg, plane_factor):
    """the twist (deg, external) the authored press path carries at this elevation, weighted out towards forward raises"""
    x = min(max(elevation_deg, PRESS_TWIST_M[0][0]), PRESS_TWIST_M[-1][0]); t = PRESS_TWIST_M[-1][1]
    for (a, ta), (b, tb) in zip(PRESS_TWIST_M, PRESS_TWIST_M[1:]):
        if a <= x <= b:
            t = ta + (tb - ta) * (x - a) / (b - a)
            break
    w = min(1.0, max(0.0, (PF_NONE - plane_factor) / (PF_NONE - PF_FULL)))
    return t * w * w * (3.0 - 2.0 * w)


def _ramp(x, k):
    """0 for x <= -k, x for x >= k, a quadratic blend between (C1): exactly zero well inside the band"""
    return 0.0 if x <= -k else (x if x >= k else (x + k) * (x + k) / (4.0 * k))


def effective_twist(raw, s, elevation_deg, plane_factor, deadband=DEADBAND_DEG):
    """the part of the raw twist (rad) outside the authored band, signed as raw"""
    ts = SIGN[s] * raw; k = math.radians(RAMP_DEG)
    hi = math.radians(press_twist_band(elevation_deg, plane_factor) + deadband); lo = -math.radians(deadband)
    return SIGN[s] * (_ramp(ts - hi, k) - _ramp(lo - ts, k))


def _turn_upperarms(rig, twist, sign):
    for s in SIDES:
        if twist.get(s):
            ub = rig.pose.bones[f"upperarm_{s}"]; d = (ub.tail - ub.head).normalized(); piv = ub.head.copy()
            ub.matrix = Matrix.Translation(piv) @ Matrix.Rotation(sign * twist[s], 4, d) @ Matrix.Translation(-piv) @ ub.matrix
            bpy.context.view_layer.update()


def drive(rig, body, r57_drive, twist=None, helpers_swing=True):
    """set the twist bones and run the r57 drives (helpers) on the swing alone.  twist: {side: rad} to use instead of the
    band rule (diagnostics: the twist a test path added).  Returns (twist used, {side: (raw deg, elevation, plane f.)})."""
    import original_v1_review_candidate_drives as r57
    import r121_drives
    bpy.context.view_layer.update()
    diag = {}
    if twist is None:
        twist = {}
        for s in SIDES:
            raw = pose_twist(rig, s); el = r57.elevation_deg(rig, s); pf = r121_drives.plane_factor(rig, s)
            diag[s] = (math.degrees(raw), el, pf)
            twist[s] = effective_twist(raw, s, el, pf)
    for s in SIDES:                                          # the twist bone counter-rotates about its own long axis
        tb = rig.pose.bones[f"upperarm_tw_{s}"]; tb.rotation_mode = "XYZ"; tb.rotation_euler = (0.0, -twist.get(s, 0.0), 0.0)
    bpy.context.view_layer.update()
    if helpers_swing:                                        # the helpers hang off the girdle: drive them with the twist
        _turn_upperarms(rig, twist, -1.0)                    # taken off the humerus, then put it back
        r57_drive(rig, body)
        _turn_upperarms(rig, twist, 1.0)
    else:
        r57_drive(rig, body)
    return twist, diag
