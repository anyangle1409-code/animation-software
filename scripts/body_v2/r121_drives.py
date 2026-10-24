"""R121 candidate drives (bpy): the arm-raise correctives of r121_arm_correctives_blender.py.  Call drive(rig, body)
after the r57 original_v1_review_candidate_drives.drive(rig, body).  No-op on a blend without the keys.

Keys R121_ARM_<s>_<deg> (authored in a sideways raise) and R121_FLEX_<s>_<deg> (forward raise, residual on top,
weighted by plane_factor): piecewise-linear hats on the humerothoracic elevation (drives.elevation_deg, as drive_s1)
through the elevations measured when each key was authored (rig["hgpt_r121_arm_angles_<s>"]), 0 below START.
CANDIDATE ONLY - not part of the runtime contract.
"""
import bpy

PREFIX = "R121_ARM_"
PROP = "hgpt_r121_arm_angles"
FLEX_PREFIX = "R121_FLEX_"
FLEX_PROP = "hgpt_r121_flex_angles"
START = 25.0


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
        for prefix, prop, gain in ((PREFIX, PROP, 1.0), (FLEX_PREFIX, FLEX_PROP, pf)):
            names = sorted((kb.name for kb in keys if kb.name.startswith(f"{prefix}{s}_")), key=lambda n: int(n.rsplit("_", 1)[1]))
            if not names or f"{prop}_{s}" not in rig:
                continue
            for name, v in _hats(names, (START,) + tuple(rig[f"{prop}_{s}"])[:len(names)], e):
                keys[name].value = v * gain
    bpy.context.view_layer.update()
