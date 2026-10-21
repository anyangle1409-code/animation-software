"""R70 top-of-press path (Claude, 21 Oct 2026).  Owner (option C, from a real dumbbell-press photo from behind): end the
press with the elbows slightly bent and flared - chosen "150 with 30": 150 deg humerothoracic elevation, 30 deg elbow
flexion, elevation plane 10 deg (was a straight 166 deg lockout, plane 15).

Identical to Work's press path (original_v1_press_extension, path v4) up to the approved marked pose (t = 0.625, 135.6 deg).
Above it, in the smoothstep parameter k (k0 = k(0.625), u = (k - k0) / (1 - k0)):
  elevation = Work's 70 + 96 k  -  (166 - 150) * smoothstep(u)                (monotonic, same slope at k0)
  elbow     = 30 + (e0 - 30) * (1 - u)^p,  e0 = 140 (1 - k0), p = 140 (1 - k0) / (e0 - 30)   (monotonic, same slope)
  plane     = 15 + (10 - 15) * smoothstep(u)
The shrug is unchanged.  Enabled with env R70_TOP="150:30:10" (elevation:elbow:plane); installed by Claude's
claude_r61_native.install, so every Claude gate copy, render and close-up uses the same path.
"""
import math
import os

T0 = 0.625
_DONE = {"on": False}


def install_path():
    spec = os.environ.get("R70_TOP", "")
    if not spec or _DONE["on"]:
        return None
    top_ht, top_elbow, top_plane = (float(x) for x in spec.split(":"))
    import original_v1_press_extension as px
    orig_state = px.press_state
    orig_pose = px.pose_press_full
    name = px._PATH["name"]
    base_plane = px.PATHS[name]["plane_deg"]
    lock = px.LOCKOUT_HT

    def _uh(t):
        k = px._smooth(t); k0 = px._smooth(T0)
        if k <= k0:
            return k, k0, 0.0, 0.0
        u = (k - k0) / (1.0 - k0)
        return k, k0, u, px._smooth(u)

    def press_state(t):
        ht, elbow, shrug = orig_state(t)
        k, k0, u, h = _uh(t)
        if u <= 0.0:
            return ht, elbow, shrug
        p = px.path()
        ht = p["start_ht"] + (lock - p["start_ht"]) * k - (lock - top_ht) * h
        e0 = p["start_elbow"] * (1.0 - k0)
        expo = p["start_elbow"] * (1.0 - k0) / (e0 - top_elbow)
        elbow = top_elbow + (e0 - top_elbow) * (1.0 - u) ** expo
        return ht, elbow, shrug

    def pose_press_full(result, t):
        _, _, _, h = _uh(t)
        px.PATHS[name]["plane_deg"] = base_plane + (top_plane - base_plane) * h
        try:
            return orig_pose(result, t)
        finally:
            px.PATHS[name]["plane_deg"] = base_plane

    px.press_state = press_state
    px.pose_press_full = pose_press_full
    _DONE["on"] = True
    print("R70_PRESS_PATH", spec, "plane", base_plane, "->", top_plane, flush=True)
    return dict(top_ht=top_ht, top_elbow=top_elbow, top_plane=top_plane)
