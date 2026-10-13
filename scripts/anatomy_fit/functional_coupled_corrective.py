"""Pure contract for the provisional W2 coupled-motion shoulder correctives (no bpy).

Seven pose-space corrective keys are solved against the PR110/PR111 coupled motion at 100..160 deg humerothoracic
elevation (10 deg spacing), each warm-started from the previous solved shape so neighbouring keys stay consistent
(an earlier two-key 120/160 blend produced 480-990 self-intersecting pairs between the keys).  Activation is a
piecewise-linear hat per key, so each key is reproduced exactly at its own pose, all keys are zero at and below
90 deg (where the coupled pose has no collapse or self-intersection), and in-between poses are linear blends of the
two neighbouring keys (measured every 5 deg, not assumed correct).

The solve targets are engineering guards, not anatomy: zero faces below 0.1 area ratio and zero self-intersecting
pairs in the shoulder region, body-volume change within +-2 %, and no posed torso skin inside the static rib guides.
"""

import math

KEY_POSES_DEG = (100.0, 110.0, 120.0, 130.0, 140.0, 150.0, 160.0)
ZERO_BELOW_DEG = 90.0
TARGETS = {
    "collapse_faces_ratio_lt_0_1": 0,
    "self_intersecting_face_pairs_in_region": 0,
    "body_volume_change_abs_pct_max": 2.0,
    "rib_guide_clearance_min_mm": 3.0,
}


def _elevation(value):
    if (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
            or not 0.0 <= value <= 160.0):
        raise ValueError("finite HT elevation 0..160 required")
    return float(value)


def key_label(angle):
    return str(int(round(angle)))


def key_weights(ht_elevation_deg):
    """Piecewise-linear hat activation over 90, KEY_POSES_DEG (weights sum to 1 above the first key)."""
    e = _elevation(ht_elevation_deg)
    knots = (ZERO_BELOW_DEG,) + KEY_POSES_DEG
    out = {key_label(k): 0.0 for k in KEY_POSES_DEG}
    if e <= ZERO_BELOW_DEG:
        return out
    for i in range(1, len(knots)):
        lo, hi = knots[i - 1], knots[i]
        if lo < e <= hi:
            t = (e - lo) / (hi - lo)
            out[key_label(hi)] = t
            if i > 1:
                out[key_label(lo)] = 1.0 - t
            return out
    return out


def taubin_coefficients(lam=0.5, mu=-0.53):
    """Taubin lambda/mu smoothing pair (shrink-free when mu < -lam < 0)."""
    if not (0.0 < lam < 1.0 and mu < -lam):
        raise ValueError("Taubin smoothing requires 0 < lambda < 1 and mu < -lambda")
    return lam, mu


def zone_falloff(ring_distance, rings):
    """Smoothing weight for a vertex `ring_distance` edges from a problem face (1 at 0, 0 beyond `rings`)."""
    if isinstance(ring_distance, bool) or not isinstance(ring_distance, int) or ring_distance < 0:
        raise ValueError("non-negative integer ring distance required")
    if isinstance(rings, bool) or not isinstance(rings, int) or rings < 1:
        raise ValueError("positive integer ring count required")
    if ring_distance > rings:
        return 0.0
    t = ring_distance / (rings + 1)
    return 1.0 - t * t * (3.0 - 2.0 * t)


def meets_targets(metrics, rib_clearance_min_mm=None):
    """Return the list of unmet engineering targets for one posed measurement (empty list means all met)."""
    unmet = []
    if metrics["collapse_faces_ratio_lt_0_1"] > TARGETS["collapse_faces_ratio_lt_0_1"]:
        unmet.append("collapse")
    if metrics["self_intersecting_face_pairs_in_region"] > TARGETS["self_intersecting_face_pairs_in_region"]:
        unmet.append("self_intersection")
    if abs(metrics["body_volume_change_pct"]) > TARGETS["body_volume_change_abs_pct_max"]:
        unmet.append("volume")
    if rib_clearance_min_mm is not None and rib_clearance_min_mm < TARGETS["rib_guide_clearance_min_mm"]:
        unmet.append("rib_clearance")
    return unmet
