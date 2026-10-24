"""R121 candidate drives (bpy): the arm-raise correctives of r121_arm_correctives_blender.py.  Call drive(rig, body)
after the r57 original_v1_review_candidate_drives.drive(rig, body).  No-op on a blend without the keys.

Keys R121_ARM_<s>_<deg> (authored in a sideways raise) and R121_FLEX_<s>_<deg> (forward raise, residual on top,
weighted by plane_factor), R121_HIP_<s>_<pct> (squat depth, hats on hip_flex_deg) R121_ELBOW_<s>_<deg> (hats on elbow_flex_deg) and R121_KNEE_<s>_<pct> (squat depth, hats on knee_flex_deg): piecewise-linear hats on the humerothoracic elevation (drives.elevation_deg, as drive_s1)
through the elevations measured when each key was authored (rig["hgpt_r121_arm_angles_<s>"]), 0 below START.
CANDIDATE ONLY - not part of the runtime contract.
"""
import bpy

PREFIX = "R121_ARM_"
PROP = "hgpt_r121_arm_angles"
FLEX_PREFIX = "R121_FLEX_"
FLEX_PROP = "hgpt_r121_flex_angles"
HIP_PREFIX = "R121_HIP_"
HIP_PROP = "hgpt_r121_hip_angles"
START = 25.0
HIP_START = 30.0
ELBOW_PREFIX = "R121_ELBOW_"
ELBOW_PROP = "hgpt_r121_elbow_angles"
ELBOW_START = 10.0
KNEE_PREFIX = "R121_KNEE_"
KNEE_PROP = "hgpt_r121_knee_angles"
KNEE_START = 20.0


def knee_flex_deg(rig, s):
    """knee flexion: angle between the posed thigh and shin directions (0 straight)"""
    import math
    u = rig.pose.bones[f"thigh_{s}"]; f = rig.pose.bones[f"shin_{s}"]
    a = (u.tail - u.head).normalized(); b = (f.tail - f.head).normalized()
    return math.degrees(math.acos(max(-1.0, min(1.0, a.dot(b)))))


def elbow_flex_deg(rig, s):
    """elbow flexion: angle between the posed upper-arm and forearm directions (0 straight)"""
    import math
    u = rig.pose.bones[f"upperarm_{s}"]; f = rig.pose.bones[f"forearm_{s}"]
    a = (u.tail - u.head).normalized(); b = (f.tail - f.head).normalized()
    return math.degrees(math.acos(max(-1.0, min(1.0, a.dot(b)))))


def hip_flex_deg(rig, s):
    """hip joint angle: between the posed thigh and where the thigh would point if it followed the pelvis rigidly"""
    pel = rig.pose.bones["pelvis"]; bp = rig.data.bones["pelvis"]
    th = rig.pose.bones[f"thigh_{s}"]; bt = rig.data.bones[f"thigh_{s}"]
    rest_dir = (bt.tail_local - bt.head_local).normalized()
    follow = (pel.matrix.to_3x3() @ bp.matrix_local.to_3x3().inverted()) @ rest_dir
    u = (th.tail - th.head).normalized()
    import math
    return math.degrees(math.acos(max(-1.0, min(1.0, u.dot(follow.normalized())))))


def plane_factor(rig, s):
    """0 for a sideways raise, 1 for a forward raise: sin^2 of the plane of elevation, from the upper arm's displacement
    relative to its rest direction (the rest arm already slants forward a little)"""
    pb = rig.pose.bones[f"upperarm_{s}"]; b = rig.data.bones[f"upperarm_{s}"]
    u = (pb.tail - pb.head).normalized(); r = (b.tail_local - b.head_local).normalized()
    d = u - r
    lat = abs(d.x); fwd = max(-d.y, 0.0)
    if lat + fwd < 1e-6:
        return 0.0
    return fwd * fwd / (lat * lat + fwd * fwd)


def _hats(names, pts, e):
    out = []
    for i, name in enumerate(names):
        lo = pts[i]
        mid = pts[i + 1] if i + 1 < len(pts) else None
        if mid is None:
            out.append((name, 0.0)); continue
        hi = pts[i + 2] if i + 2 < len(pts) else None
        if e <= lo:
            v = 0.0
        elif e <= mid:
            v = (e - lo) / (mid - lo)
        elif hi is None:
            v = 1.0
        else:
            v = max(0.0, (hi - e) / (hi - mid))
        out.append((name, v))
    return out


def drive(rig, body):
    import original_v1_review_candidate_drives as drives
    if not body.data.shape_keys:
        return
    keys = body.data.shape_keys.key_blocks
    for s in ("l", "r"):
        e = drives.elevation_deg(rig, s)
        pf = plane_factor(rig, s)
        hf = hip_flex_deg(rig, s)
        for prefix, prop, gain, ang, start in ((PREFIX, PROP, 1.0, e, START), (FLEX_PREFIX, FLEX_PROP, pf, e, START),
                                               (HIP_PREFIX, HIP_PROP, 1.0, hf, HIP_START),
                                               (ELBOW_PREFIX, ELBOW_PROP, 1.0, elbow_flex_deg(rig, s), ELBOW_START),
                                               (KNEE_PREFIX, KNEE_PROP, 1.0, knee_flex_deg(rig, s), KNEE_START)):
            names = sorted((kb.name for kb in keys if kb.name.startswith(f"{prefix}{s}_")), key=lambda n: int(n.rsplit("_", 1)[1]))
            if not names or f"{prop}_{s}" not in rig:
                continue
            for name, v in _hats(names, (start,) + tuple(rig[f"{prop}_{s}"])[:len(names)], ang):
                keys[name].value = v * gain
    bpy.context.view_layer.update()
