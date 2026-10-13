"""Reference-constrained corrections of the provisional W1/W2 shoulder/thorax guides (pure Python).

PROVISIONAL authored guides, never registered bone surfaces, contact evidence or a cohort fit.

Ribs
  The PR109/PR110 rib guide was the straight a003 head->tail chord plus a pure +-X sin^2 bow of 90-150 mm, which
  reads as a steep coil and leaves ribs 6-12 partly outside the original skin.  The corrected guide keeps the frozen
  a003 endpoints and draws the Holcombe in-plane rib shape on them:
    * distal segment (peak -> costochondral end): the exact Holcombe 2016 logarithmic spiral (Eqs. 2.2-2.7), already
      implemented and independently tested in rib_spiral_reconstruction.py, with the Holcombe 2017 population-mean
      Xpk, Ypk and Bd of the rib level;
    * proximal segment (head -> peak): Holcombe's proximal spiral branch selection is BLOCKED in this repository
      (rib_inplane_derivation_holcombe2016_v1.json), so it is NOT used.  An authored C1 cubic bridge is used instead,
      constrained only by the published proximal inner angle phi_pia (start tangent) and the published peak
      (horizontal tangent at [Xpk, Ypk], matching the distal spiral's stationary peak).  It is labelled authored.
  The in-plane frame: x along the a003 chord, y towards the outward-lateral direction orthogonal to the chord (an
  authored orientation; Holcombe's pump-handle/lateral-swing/bucket-handle convention is not mapped and is not
  claimed).

Scapula
  The guide similarity-fitted the Lee-2024-sized c004 landmark outline onto the a003 anatomical scapula control stick,
  which is 1.39x longer than the record's glenoid->inferior-angle segment, inflating every distance by 39 %.  The
  corrected guide is RIGID (scale 1): the outline keeps the record's Lee-consistent size, its glenoid end stays on
  the a003 scapula head, and its long axis follows the a003 stick direction.  A bounded rotation about the glenoid
  (place_on_thorax) then sets the medial-border clearance to the rib guides.

Humeral axial rotation
  Measured in an anatomical-style humeral frame: angle, about the shaft, from the elevation-plane normal to the
  elbow-flexion (epicondylar proxy) axis.  The external-rotation magnitude is a project-authored hypothesis
  (direction only follows the reported healthy pattern of increasing humeral external rotation with elevation);
  no cohort trajectory is fitted or claimed.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from functional_original_attachment import fit_segment_similarity
from rib_spiral_reconstruction import distal_curve

ROOT = Path(__file__).resolve().parents[2]
HOLCOMBE_PATH = ROOT / "ORIGINAL_V1_WORK/anatomy/rib_demographic_model_holcombe2017_v1.json"
LEE_PATH = ROOT / "ORIGINAL_V1_WORK/anatomy/canonical_scapula_measured_landmark_model_v1.json"

RIB_SCOPE = "Holcombe distal spiral + authored phi_pia/peak-constrained proximal bridge on frozen a003 endpoints"
HUMERAL_AXIAL_TOP_DEG = 35.0      # authored external rotation at 160 deg HT elevation (hypothesis, not a fit)


def _finite_point(p, n=3):
    if not isinstance(p, (list, tuple)) or len(p) != n:
        raise ValueError(f"expected finite {n}D point")
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in p):
        raise ValueError(f"expected finite {n}D point")
    return tuple(float(v) for v in p)


def load_holcombe(path=HOLCOMBE_PATH):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def rib_level_parameters(model, level):
    if isinstance(level, bool) or not isinstance(level, int) or not 1 <= level <= 12:
        raise ValueError("rib level 1..12 required")
    m = model["levels"][str(level)]["population_mean"]
    return {"Xpk": float(m["Xpk"]), "Ypk": float(m["Ypk"]), "Bd": float(m["Bd"]),
            "phi_pia_deg": float(m["phi_pia_deg"]), "Sx_mm": float(m["Sx_mm"])}


def _bezier(p0, p1, p2, p3, t):
    u = 1.0 - t
    return tuple(u ** 3 * a + 3 * u * u * t * b + 3 * u * t * t * c + t ** 3 * d for a, b, c, d in zip(p0, p1, p2, p3))


def rib_inplane_curve(params, proximal_samples=24, distal_samples=33):
    """Normalized in-plane rib curve from [0,0] (head) through [Xpk,Ypk] (peak) to [1,0] (anterior end)."""
    xpk, ypk, phi = params["Xpk"], params["Ypk"], math.radians(params["phi_pia_deg"])
    if not (0.05 <= xpk <= 0.8 and 0.05 <= ypk <= 0.9):
        raise ValueError("peak outside the Holcombe 2016 parameter bounds")
    alpha = math.atan2(ypk, xpk)
    if not alpha < phi < math.pi:
        raise ValueError("phi_pia must exceed the peak angle (Holcombe constraint) and stay below 180 deg")
    # Start tangent at phi from the chord; its handle never rises above 60 % of the peak height, and the peak handle
    # is horizontal (the distal spiral's peak is a stationary maximum, so the join is C1).
    k0 = min(0.6 * ypk / math.sin(phi), 0.5 * math.hypot(xpk, ypk))
    p0, p3 = (0.0, 0.0), (xpk, ypk)
    p1 = (k0 * math.cos(phi), k0 * math.sin(phi))
    p2 = (xpk - 0.45 * max(xpk - min(p1[0], 0.0), 1e-6), ypk)
    proximal = [_bezier(p0, p1, p2, p3, i / (proximal_samples - 1)) for i in range(proximal_samples)]
    distal = [tuple(p) for p in distal_curve(xpk, ypk, params["Bd"], samples=distal_samples)]
    curve = proximal[:-1] + distal
    if max(y for _, y in curve) > ypk + 1e-9:
        raise ValueError("authored proximal bridge overshoots the published peak")
    return curve


def _sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _norm(a):
    return math.sqrt(_dot(a, a))


def _unit(a):
    n = _norm(a)
    if n <= 1e-12:
        raise ValueError("collapsed axis")
    return tuple(x / n for x in a)


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def rib_points_reference(head, tail, side, params):
    """3D rib guide on the frozen a003 endpoints (frame: +X anatomical left, +Y posterior, +Z superior)."""
    head, tail = _finite_point(head), _finite_point(tail)
    if side not in ("left", "right"):
        raise ValueError("explicit anatomical side required")
    sign = 1.0 if side == "left" else -1.0
    if head[0] * sign <= 0 or tail[0] * sign <= 0:
        raise ValueError("rib endpoints disagree with declared anatomical side")
    chord = _sub(tail, head)
    length = _norm(chord)
    if length < 0.01:
        raise ValueError("collapsed rib endpoints")
    ex = tuple(c / length for c in chord)
    outward = (sign, 0.0, 0.0)
    ey = _sub(outward, tuple(_dot(outward, ex) * c for c in ex))
    ey = _unit(ey)
    pts = [tuple(head[k] + length * (u * ex[k] + v * ey[k]) for k in range(3)) for u, v in rib_inplane_curve(params)]
    pts[0], pts[-1] = head, tail
    return pts


def fit_segment_rigid(points, source_head, source_tail, target_head, target_tail):
    """Rotate/translate (scale 1) points so source_head->tail aligns with the target segment direction at target_head."""
    sh, st = _finite_point(source_head), _finite_point(source_tail)
    th, tt = _finite_point(target_head), _finite_point(target_tail)
    src_len, tgt_len = _norm(_sub(st, sh)), _norm(_sub(tt, th))
    if src_len <= 1e-12 or tgt_len <= 1e-12:
        raise ValueError("collapsed segment")
    # Re-use the reviewed similarity fit with the target tail moved onto the source length (scale exactly 1).
    direction = tuple(c / tgt_len for c in _sub(tt, th))
    rigid_tail = tuple(th[k] + src_len * direction[k] for k in range(3))
    pts = [_finite_point(p) for p in points]
    out = fit_segment_similarity(pts, sh, st, th, rigid_tail)
    # fit_segment_similarity snaps exact head/tail inputs; the tail snap is the rigid tail, so scale stays 1.
    return out


def rotate_about(point, pivot, axis, angle_rad):
    p, c, k = _finite_point(point), _finite_point(pivot), _unit(_finite_point(axis))
    v = _sub(p, c)
    cs, sn = math.cos(angle_rad), math.sin(angle_rad)
    kxv = _cross(k, v)
    kd = _dot(k, v)
    r = tuple(v[i] * cs + kxv[i] * sn + k[i] * kd * (1 - cs) for i in range(3))
    return tuple(c[i] + r[i] for i in range(3))


def place_on_thorax(landmarks, pivot, clearance_fn, medial_indices, target_clearance_m, limit_deg=25.0, step_deg=1.0):
    """Grid-search a rotation about the glenoid pivot (yaw about +Z, then tilt about +X) minimising the squared error
    of the medial-border landmarks' clearance to the thorax guide against target_clearance_m.  Returns
    (yaw_deg, tilt_deg, rms_error_m, rotated_landmarks).  Bounded, deterministic, no contact solver."""
    pts = [_finite_point(p) for p in landmarks]
    if not medial_indices or any(i < 0 or i >= len(pts) for i in medial_indices):
        raise ValueError("medial landmark indices out of range")
    if not (math.isfinite(target_clearance_m) and 0.0 <= target_clearance_m <= 0.05):
        raise ValueError("target clearance must be 0..50 mm")
    best = None
    steps = int(round(limit_deg / step_deg))
    for iy in range(-steps, steps + 1):
        for it in range(-steps, steps + 1):
            yaw, tilt = iy * step_deg, it * step_deg
            err = 0.0
            for i in medial_indices:
                q = rotate_about(pts[i], pivot, (0.0, 0.0, 1.0), math.radians(yaw))
                q = rotate_about(q, pivot, (1.0, 0.0, 0.0), math.radians(tilt))
                err += (clearance_fn(q) - target_clearance_m) ** 2
            key = (err, abs(yaw) + abs(tilt))
            if best is None or key < best[0]:
                best = (key, yaw, tilt)
    (_, _), yaw, tilt = best[0], best[1], best[2]
    out = []
    for p in pts:
        q = rotate_about(p, pivot, (0.0, 0.0, 1.0), math.radians(yaw))
        out.append(rotate_about(q, pivot, (1.0, 0.0, 0.0), math.radians(tilt)))
    rms = math.sqrt(best[0][0] / len(medial_indices))
    return yaw, tilt, rms, out


def humeral_external_rotation_deg(ht_elevation_deg):
    """Authored external-rotation hypothesis (smoothstep 0 -> HUMERAL_AXIAL_TOP_DEG over 0..160 deg)."""
    if (isinstance(ht_elevation_deg, bool) or not isinstance(ht_elevation_deg, (int, float))
            or not math.isfinite(ht_elevation_deg) or not 0.0 <= ht_elevation_deg <= 160.0):
        raise ValueError("finite HT elevation 0..160 required")
    t = ht_elevation_deg / 160.0
    return HUMERAL_AXIAL_TOP_DEG * t * t * (3.0 - 2.0 * t)


def external_rotation_sign(side):
    """Sign of external rotation about the DISTAL shaft direction (right-hand rule) for an anatomical side.

    Anatomical right (-X lateral): +; anatomical left (+X lateral): -.  Checked by test: a hanging arm's anterior
    probe gains a lateral component under external rotation.
    """
    if side not in ("left", "right"):
        raise ValueError("explicit anatomical side required")
    return 1.0 if side == "right" else -1.0


def humeral_axial_angle_deg(shaft_dir, elbow_axis, plane_deg, side):
    """Signed angle about the shaft from the elevation-plane normal to the elbow axis (both projected off the shaft).

    The elevation plane of an anatomical side contains the vertical and that side's horizontal azimuth
    (lateral * cos p, -sin p, 0) (HGPT +X anatomical left, -Y anterior; p from the coronal plane towards anterior,
    the PR110 convention).  Its normal (azimuth x +Z) is defined at every elevation, including 0 deg.
    """
    d = _unit(_finite_point(shaft_dir))
    e = _finite_point(elbow_axis)
    if side not in ("left", "right"):
        raise ValueError("explicit anatomical side required")
    lateral = 1.0 if side == "left" else -1.0
    p = math.radians(plane_deg)
    az = (lateral * math.cos(p), -math.sin(p), 0.0)
    n = _cross(az, (0.0, 0.0, 1.0))
    def proj(v):
        return _unit(_sub(v, tuple(_dot(v, d) * c for c in d)))
    a, b = proj(n), proj(e)
    return math.degrees(math.atan2(_dot(_cross(a, b), d), max(-1.0, min(1.0, _dot(a, b)))))


def lee_reference_distances(path=LEE_PATH):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    return {k: {"pair_1based": v["landmark_pair_1based"], "pred_mm": v["direct_stature_regression"]["predicted"],
                "resid_sd_mm": v["direct_stature_regression"]["residual_sd"]}
            for k, v in d["groups"]["all_males"]["distances_mm"].items()}
