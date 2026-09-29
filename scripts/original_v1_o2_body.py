"""ORIGINAL v1 O2 body generator — project-authored, clean-room.

Inputs are limited to:
  * ORIGINAL_V1_WORK/hgpt_canonical_v4_original.json (committed v4 rest payload)
  * the anatomical measurements authored in this file.
No mesh, weight, UV, projection or surface from any other character is read.

The generator builds a quad control cage whose loops follow the v4 joints
(split junctions at axillae, crotch, thumb web and finger webs), applies one
Catmull-Clark subdivision in plain Python, and returns vertices/faces in
Blender coordinates (Z up, character forward = -Y, `_l` bones at -X).

Internally points are (x, f, z) with f = forward = -Y.
Pure numpy: runs under Blender's bundled Python without bpy.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RIG_PAYLOAD = ROOT / "ORIGINAL_V1_WORK" / "hgpt_canonical_v4_original.json"
GENERATOR_VERSION = "o2-body-1"
TARGET_HEIGHT = 1.82

FWD = np.array([0.0, 1.0, 0.0])
UP = np.array([0.0, 0.0, 1.0])


# --------------------------------------------------------------------------
# Rig input (left side only; right side is an exact mirror by construction)
# --------------------------------------------------------------------------

def load_rig(path: Path = RIG_PAYLOAD) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    bones = {}
    for item in payload["bones"]:
        # Project +Y up, +Z forward -> internal (x, f, z) with f = project z.
        head = np.array([item["head"][0], item["head"][2], item["head"][1]])
        tail = np.array([item["tail"][0], item["tail"][2], item["tail"][1]])
        bones[item["name"]] = (head, tail)
    return bones


def lat(bones, name, end="head"):
    """Bone point for the left side expressed with lateral distance lx >= 0."""
    head, tail = bones[name]
    p = head if end == "head" else tail
    return np.array([-p[0], p[1], p[2]])  # _l bones sit at -X


# --------------------------------------------------------------------------
# Geometry helpers
# --------------------------------------------------------------------------

def centripetal_cr(points, closed=False, samples=32):
    P = [np.asarray(p, float) for p in points]
    n = len(P)
    segs = n if closed else n - 1
    out = []
    for i in range(segs):
        if closed:
            p0, p1, p2, p3 = P[(i - 1) % n], P[i], P[(i + 1) % n], P[(i + 2) % n]
        else:
            p1, p2 = P[i], P[i + 1]
            p0 = P[i - 1] if i > 0 else p1 + (p1 - p2)
            p3 = P[i + 2] if i + 2 < n else p2 + (p2 - p1)
        def tj(ti, a, b):
            return ti + max(np.linalg.norm(b - a), 1e-9) ** 0.5
        t0 = 0.0
        t1 = tj(t0, p0, p1)
        t2 = tj(t1, p1, p2)
        t3 = tj(t2, p2, p3)
        for k in range(samples):
            t = t1 + (t2 - t1) * k / samples
            a1 = (t1 - t) / (t1 - t0) * p0 + (t - t0) / (t1 - t0) * p1
            a2 = (t2 - t) / (t2 - t1) * p1 + (t - t1) / (t2 - t1) * p2
            a3 = (t3 - t) / (t3 - t2) * p2 + (t - t2) / (t3 - t2) * p3
            b1 = (t2 - t) / (t2 - t0) * a1 + (t - t0) / (t2 - t0) * a2
            b2 = (t3 - t) / (t3 - t1) * a2 + (t - t1) / (t3 - t1) * a3
            out.append((t2 - t) / (t2 - t1) * b1 + (t - t1) / (t2 - t1) * b2)
    if not closed:
        out.append(P[-1])
    return np.array(out)


def resample_open(curve, count):
    d = np.linalg.norm(np.diff(curve, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(d)])
    targets = np.linspace(0.0, s[-1], count)
    return np.stack([np.interp(targets, s, curve[:, j]) for j in range(3)], axis=1)


def sample_path(control, count):
    """Open curve through control points, `count` points equally spaced incl. ends."""
    return resample_open(centripetal_cr(control, closed=False), count)


def to_left(p):
    """(lx, f, z) authored for the left side -> internal (x, f, z)."""
    return np.array([-p[0], p[1], p[2]], float)


def mirror(p):
    return np.array([-p[0], p[1], p[2]], float)


def unit(v):
    v = np.asarray(v, float)
    n = np.linalg.norm(v)
    return v / n if n > 1e-12 else v


def periodic_profile(spec):
    """spec: {angle_deg: radius} -> r(phi) with periodic Catmull-Rom interpolation."""
    items = sorted((a % 360.0, r) for a, r in spec.items())
    angles = np.radians([a for a, _ in items])
    radii = np.array([r for _, r in items], float)
    n = len(angles)

    def r(phi):
        phi = phi % (2 * math.pi)
        i = np.searchsorted(angles, phi, side="right") - 1
        i %= n
        j = (i + 1) % n
        a0 = angles[i]
        a1 = angles[j] if j != 0 or n == 1 else angles[0] + 2 * math.pi
        if a1 <= a0:
            a1 += 2 * math.pi
        x = phi if phi >= a0 else phi + 2 * math.pi
        t = (x - a0) / (a1 - a0)
        p0, p1, p2, p3 = radii[(i - 1) % n], radii[i], radii[j], radii[(j + 1) % n]
        return 0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                      + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)
    return r


def coons_grid(bottom, right, top, left):
    """Boundary sides as point arrays: bottom[0]=left[0], bottom[-1]=right[0],
    top[0]=left[-1], top[-1]=right[-1]. Returns grid[j][i] (j along left)."""
    nb = len(bottom) - 1
    na = len(left) - 1
    P00, P10, P01, P11 = bottom[0], bottom[-1], top[0], top[-1]
    grid = [[None] * (nb + 1) for _ in range(na + 1)]
    for j in range(na + 1):
        v = j / na
        for i in range(nb + 1):
            u = i / nb
            grid[j][i] = ((1 - v) * bottom[i] + v * top[i] + (1 - u) * left[j] + u * right[j]
                          - ((1 - u) * (1 - v) * P00 + u * (1 - v) * P10
                             + (1 - u) * v * P01 + u * v * P11))
    return grid


# --------------------------------------------------------------------------
# Mesh builder
# --------------------------------------------------------------------------

class Builder:
    def __init__(self):
        self.v: list[np.ndarray] = []
        self.f: list[tuple[int, ...]] = []
        self.regions: dict[str, set[int]] = {}

    def add(self, p, region=None) -> int:
        self.v.append(np.asarray(p, float))
        idx = len(self.v) - 1
        if region:
            self.regions.setdefault(region, set()).add(idx)
        return idx

    def add_many(self, pts, region=None) -> list[int]:
        return [self.add(p, region) for p in pts]

    def pos(self, ids):
        return np.array([self.v[i] for i in ids])

    def bridge(self, a, b):
        n = len(a)
        assert n == len(b), (n, len(b))
        for k in range(n):
            self.f.append((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))

    def bridge_aligned(self, a, b):
        """Bridge closed loops, re-indexing b for minimum twist."""
        n = len(a)
        A, Bp = self.pos(a), self.pos(b)
        best = None
        for direction in (1, -1):
            for off in range(n):
                idx = [(off + direction * k) % n for k in range(n)]
                cost = float(np.sum(np.linalg.norm(A - Bp[idx], axis=1)))
                if best is None or cost < best[0]:
                    best = (cost, [b[i] for i in idx])
        self.bridge(a, best[1])
        return best[1]

    def cap(self, loop, a, b, dome=0.0, dome_dir=None, start=0, region=None):
        """Close a loop of 2(a+b) verts with an a x b quad grid (Coons patch).
        Corners at start, start+b, start+b+a, start+2b+a."""
        n = len(loop)
        assert n == 2 * (a + b), (n, a, b)
        L = [loop[(start + k) % n] for k in range(n)]
        bottom_ids = L[0:b + 1]
        right_ids = L[b:b + a + 1]
        top_ids = list(reversed(L[b + a:2 * b + a + 1]))
        left_ids = list(reversed(L[2 * b + a:] + [L[0]]))
        grid = coons_grid(self.pos(bottom_ids), self.pos(right_ids),
                          self.pos(top_ids), self.pos(left_ids))
        pts = self.pos(loop)
        normal = unit(dome_dir) if dome_dir is not None else np.zeros(3)
        ids = [[None] * (b + 1) for _ in range(a + 1)]
        for i in range(b + 1):
            ids[0][i] = bottom_ids[i]
            ids[a][i] = top_ids[i]
        for j in range(a + 1):
            ids[j][0] = left_ids[j]
            ids[j][b] = right_ids[j]
        for j in range(1, a):
            for i in range(1, b):
                u, v = i / b, j / a
                bump = 16 * u * (1 - u) * v * (1 - v)
                ids[j][i] = self.add(grid[j][i] + normal * dome * bump, region)
        for j in range(a):
            for i in range(b):
                self.f.append((ids[j][i], ids[j][i + 1], ids[j + 1][i + 1], ids[j + 1][i]))
        del pts
        return ids

    def loft(self, start, rings, blend=3, region=None):
        """Loft rings from an existing closed loop.
        rings: list of (center, e1, e2, profile) with profile(phi)->radius and
        phi measured from e1 toward e2. Vertex correspondence follows the start
        loop's angles and relaxes to equal arc length over `blend` rings."""
        n = len(start)
        c0, e10, e20, _ = rings[0]
        rel = self.pos(start) - c0
        ang = np.unwrap(np.arctan2(rel @ e20, rel @ e10))
        direction = 1.0 if ang[-1] > ang[0] else -1.0
        prev = start
        for i, (c, e1, e2, prof) in enumerate(rings):
            w = min(1.0, (i + 1) / blend)
            uni = uniform_arc_angles(prof, n, ang[0], direction)
            phis = (1 - w) * ang + w * uni
            ids = [self.add(c + prof(p) * (math.cos(p) * e1 + math.sin(p) * e2), region)
                   for p in phis]
            self.bridge(prev, ids)
            prev = ids
            ang = phis
        return prev


def uniform_arc_angles(prof, n, start, direction):
    dense = np.linspace(0, 2 * math.pi, 721)
    pts = np.array([[prof(a) * math.cos(a), prof(a) * math.sin(a)] for a in dense])
    s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    total = s[-1]
    s0 = np.interp(start % (2 * math.pi), dense, s)
    out = []
    for k in range(n):
        target = (s0 + direction * total * k / n) % total
        out.append(np.interp(target, s, dense))
    out = np.unwrap(np.array(out))
    # keep the start angle's branch
    out += start - out[0]
    return out


# --------------------------------------------------------------------------
# Ring constructors (symmetric about x = 0)
# --------------------------------------------------------------------------

def ring32_from_half(control):
    """control: (lx, f, z) front-centre -> back-centre for the left half.
    Returns 32 points: 0 front centre, 1..15 left (x<0), 16 back, 17..31 right."""
    half = sample_path([to_left(p) for p in control], 17)
    half[0][0] = 0.0
    half[16][0] = 0.0
    ring = [half[i] for i in range(17)]
    ring += [mirror(half[32 - i]) for i in range(17, 32)]
    return ring


def superellipse_half(z, W, front, back, fm=None, n=2.4, bumps=(), n_back=None):
    """Torso half-profile control (lx, f, z) from front centre to back centre.
    n_back (optional) makes the back half broader/flatter than the front."""
    if fm is None:
        fm = 0.5 * (front + back)
    df, db = front - fm, fm - back
    nb = n_back or n
    pts = []
    for t in np.linspace(0.0, math.pi, 25):
        c, s = math.cos(t), math.sin(t)
        e = n if c >= 0 else nb
        lx = W * abs(s) ** (2 / e)
        f = fm + (df if c >= 0 else db) * math.copysign(abs(c) ** (2 / e), c)
        off = sum(a * math.exp(-((t - tc) / w) ** 2) for tc, w, a in bumps)
        d = unit(np.array([lx, f - fm]))
        pts.append((lx + d[0] * off, f + d[1] * off, z))
    return pts


def ring60(front_half, arm_path, back_half):
    """Wide shoulder ring. front_half: centre->F (7 pts), arm_path: F->B (18),
    back_half: B->back centre (8). All (lx, f, z) left side."""
    fr = sample_path([to_left(p) for p in front_half], 7)
    ar = sample_path([to_left(p) for p in arm_path], 18)
    bk = sample_path([to_left(p) for p in back_half], 8)
    fr[0][0] = 0.0
    bk[-1][0] = 0.0
    left = list(fr) + list(ar[1:-1]) + list(bk)  # a0..a30 (31 pts)
    assert len(left) == 31
    ring = left + [mirror(left[60 - i]) for i in range(31, 60)]
    return ring


# --------------------------------------------------------------------------
# Anatomy (authored). Units metres; (lx, f, z) left side.
# --------------------------------------------------------------------------

# Torso rings below the axilla: z, half-breadth, front f, back f, exponent, bumps
TORSO_LEVELS = [
    # z,     W,     front,  back,   n,   bumps (t, width, amount)
    # Sagittal placement follows the v4 plumb line (ear/shoulder/hip joints near
    # f=0): sternal notch just ahead of the clavicle heads, upper back just
    # outside the scapula bone tails (f=-0.145), lumbar lordosis at the waist.
    # Glutes: lateral-posterior bulge plus the intergluteal cleft at the back centre.
    (0.885, 0.164, 0.072, -0.132, 2.3, [(2.55, 0.35, 0.020), (math.pi, 0.10, -0.022), (1.05, 0.25, -0.008)]),
    (0.930, 0.168, 0.086, -0.140, 2.4, [(2.55, 0.40, 0.022), (math.pi, 0.10, -0.018), (1.05, 0.25, -0.004)]),
    (0.980, 0.162, 0.096, -0.130, 2.4, [(2.60, 0.40, 0.014), (math.pi, 0.12, -0.010)]),
    (1.030, 0.150, 0.102, -0.102, 2.4, [(math.pi, 0.25, -0.006)]),
    # athletic V-taper: narrow waist, lats flaring toward the axilla
    (1.080, 0.139, 0.104, -0.084, 2.4, [(math.pi, 0.22, -0.009), (2.75, 0.2, 0.006)]),
    (1.130, 0.133, 0.103, -0.083, 2.3, [(math.pi, 0.22, -0.009), (2.75, 0.2, 0.007)]),
    (1.180, 0.137, 0.104, -0.096, 2.3, [(math.pi, 0.22, -0.008), (2.75, 0.2, 0.005)], 2.6),
    (1.230, 0.147, 0.108, -0.121, 2.3, [(math.pi, 0.22, -0.007), (1.95, 0.35, 0.006), (2.55, 0.30, 0.008)], 3.0),
    (1.280, 0.156, 0.111, -0.147, 2.3, [(math.pi, 0.22, -0.009), (0.55, 0.30, 0.005), (1.95, 0.35, 0.009), (2.55, 0.30, 0.013)], 3.3),
    (1.330, 0.159, 0.118, -0.156, 2.3, [(math.pi, 0.22, -0.010), (0.52, 0.34, 0.018), (0.0, 0.12, -0.006), (1.95, 0.35, 0.009), (2.55, 0.30, 0.012)], 3.4),
    (1.370, 0.159, 0.118, -0.155, 2.3, [(math.pi, 0.22, -0.010), (0.52, 0.34, 0.019), (0.0, 0.12, -0.006), (1.95, 0.35, 0.008), (2.55, 0.30, 0.008)], 3.2),
]
# How strongly each torso ring's vertex columns are steered toward the axilla
# fold/chain columns of ring A (index-aligned with TORSO_LEVELS).
TORSO_COLUMN_STEER = [0, 0, 0, 0, 0, 0, 0, 0.12, 0.30, 0.55, 0.80]

# Shoulder rings (60 verts): front half centre->F, arm path F->B, back half B->centre.
SHOULDER_RINGS = [
    dict(  # A: axilla level — arm part matches the first arm ring below
        front=[(0.0, 0.114, 1.400), (0.050, 0.128, 1.400), (0.105, 0.120, 1.401), (0.142, 0.092, 1.398), (0.156, 0.052, 1.390)],
        arm=[(0.156, 0.052, 1.390), (0.184, 0.030, 1.396), (0.222, 0.023, 1.400), (0.258, 0.002, 1.400),
             (0.278, -0.032, 1.400), (0.262, -0.070, 1.400), (0.228, -0.094, 1.400),
             (0.192, -0.098, 1.400), (0.166, -0.092, 1.400)],
        back=[(0.166, -0.092, 1.400), (0.148, -0.126, 1.402), (0.105, -0.150, 1.402), (0.048, -0.156, 1.400), (0.0, -0.150, 1.400)],
    ),
    dict(  # S1: humeral head level, deltoid wraps the joint
        front=[(0.0, 0.096, 1.448), (0.050, 0.108, 1.448), (0.100, 0.100, 1.452), (0.136, 0.074, 1.458), (0.150, 0.046, 1.462)],
        arm=[(0.150, 0.046, 1.462), (0.182, 0.040, 1.458), (0.225, 0.032, 1.452), (0.264, 0.008, 1.450),
             (0.285, -0.032, 1.450), (0.268, -0.076, 1.452), (0.234, -0.104, 1.456),
             (0.190, -0.114, 1.460), (0.152, -0.118, 1.464)],
        back=[(0.152, -0.118, 1.464), (0.120, -0.140, 1.460), (0.075, -0.150, 1.455), (0.035, -0.148, 1.450), (0.0, -0.143, 1.448)],
    ),
    dict(  # S2: acromial level
        front=[(0.0, 0.066, 1.494), (0.045, 0.070, 1.496), (0.085, 0.068, 1.500), (0.112, 0.060, 1.506), (0.125, 0.054, 1.510)],
        arm=[(0.125, 0.054, 1.510), (0.170, 0.050, 1.504), (0.220, 0.038, 1.498), (0.258, 0.010, 1.495),
             (0.278, -0.032, 1.495), (0.262, -0.076, 1.498), (0.228, -0.104, 1.503),
             (0.174, -0.116, 1.509), (0.125, -0.118, 1.514)],
        back=[(0.125, -0.118, 1.514), (0.090, -0.130, 1.510), (0.050, -0.132, 1.505), (0.020, -0.128, 1.501), (0.0, -0.125, 1.500)],
    ),
    dict(  # S3: top ring (sternal notch / clavicle / acromion / trapezius), rising toward the neck
        front=[(0.0, 0.036, 1.515), (0.025, 0.037, 1.524), (0.045, 0.035, 1.537), (0.058, 0.030, 1.549), (0.064, 0.024, 1.557)],
        arm=[(0.064, 0.024, 1.557), (0.110, 0.034, 1.537), (0.170, 0.030, 1.532), (0.222, 0.018, 1.530),
             (0.252, -0.020, 1.522), (0.242, -0.070, 1.525), (0.200, -0.098, 1.537),
             (0.135, -0.102, 1.556), (0.064, -0.074, 1.584)],
        back=[(0.064, -0.074, 1.584), (0.048, -0.082, 1.586), (0.030, -0.088, 1.585), (0.014, -0.091, 1.583), (0.0, -0.092, 1.582)],
    ),
]
AXILLA_CHAIN = [(0.182, 0.008, 1.426), (0.183, -0.058, 1.424)]          # F_l -> B_l
NECK_SIDE_CHAIN = [(0.066, 0.002, 1.576), (0.066, -0.038, 1.585)]        # F_l -> B_l (top)
SHOULDER_CAP_DOME = 0.006

NECK_RINGS = [  # athletic neck: sternocleidomastoid/trapezius mass
    [(0.0, 0.048, 1.583), (0.044, 0.038, 1.590), (0.066, -0.004, 1.602), (0.064, -0.046, 1.606), (0.034, -0.078, 1.607), (0.0, -0.082, 1.607)],
    [(0.0, 0.054, 1.602), (0.043, 0.044, 1.607), (0.063, 0.001, 1.616), (0.061, -0.043, 1.621), (0.032, -0.074, 1.623), (0.0, -0.079, 1.623)],
]

HEAD_RINGS = [
    # Neutral anatomical head (no eye/mouth openings at O2). Each ring runs
    # front centre -> cheek -> side -> back centre; the back rises toward the
    # occiput so the nape/skull base forms naturally.
    # under-jaw (throat to chin)
    [(0.0, 0.092, 1.604), (0.030, 0.084, 1.608), (0.050, 0.055, 1.622), (0.062, 0.010, 1.636), (0.056, -0.040, 1.642), (0.030, -0.068, 1.643), (0.0, -0.074, 1.643)],
    # chin / mandible angle
    [(0.0, 0.108, 1.620), (0.020, 0.104, 1.621), (0.042, 0.080, 1.628), (0.062, 0.030, 1.645), (0.068, -0.010, 1.656), (0.060, -0.055, 1.660), (0.0, -0.085, 1.662)],
    # mouth
    [(0.0, 0.110, 1.645), (0.020, 0.106, 1.645), (0.038, 0.090, 1.646), (0.060, 0.050, 1.656), (0.072, 0.000, 1.668), (0.064, -0.062, 1.674), (0.0, -0.094, 1.676)],
    # upper lip
    [(0.0, 0.114, 1.662), (0.016, 0.110, 1.662), (0.036, 0.094, 1.664), (0.058, 0.060, 1.668), (0.074, 0.000, 1.680), (0.066, -0.068, 1.688), (0.0, -0.099, 1.690)],
    # nose base / cheek
    [(0.0, 0.118, 1.674), (0.012, 0.114, 1.676), (0.030, 0.096, 1.678), (0.056, 0.070, 1.680), (0.075, 0.005, 1.692), (0.068, -0.072, 1.700), (0.0, -0.102, 1.702)],
    # nose tip / cheekbone
    [(0.0, 0.128, 1.690), (0.012, 0.118, 1.690), (0.028, 0.094, 1.692), (0.056, 0.078, 1.694), (0.076, 0.005, 1.704), (0.069, -0.074, 1.712), (0.0, -0.104, 1.714)],
    # eyes / nose bridge (sockets slightly recessed)
    [(0.0, 0.106, 1.712), (0.012, 0.100, 1.712), (0.030, 0.084, 1.712), (0.052, 0.080, 1.713), (0.073, 0.020, 1.720), (0.070, -0.076, 1.726), (0.0, -0.105, 1.728)],
    # brow ridge
    [(0.0, 0.102, 1.733), (0.020, 0.100, 1.733), (0.040, 0.094, 1.734), (0.060, 0.070, 1.736), (0.074, 0.015, 1.742), (0.070, -0.078, 1.746), (0.0, -0.104, 1.748)],
    # forehead / parietal
    [(0.0, 0.096, 1.760), (0.030, 0.092, 1.760), (0.056, 0.068, 1.762), (0.072, 0.020, 1.766), (0.074, -0.030, 1.768), (0.064, -0.076, 1.768), (0.0, -0.098, 1.768)],
    [(0.0, 0.080, 1.786), (0.032, 0.074, 1.787), (0.056, 0.048, 1.789), (0.068, 0.005, 1.791), (0.066, -0.040, 1.791), (0.052, -0.072, 1.790), (0.0, -0.085, 1.789)],
    [(0.0, 0.056, 1.806), (0.030, 0.050, 1.807), (0.048, 0.025, 1.808), (0.054, -0.010, 1.809), (0.050, -0.045, 1.809), (0.036, -0.064, 1.808), (0.0, -0.068, 1.807)],
]
CROWN_DOME = 0.016

CROTCH_CHAIN = [(0.0, 0.040, 0.848), (0.0, -0.010, 0.836), (0.0, -0.065, 0.850)]  # front -> back

# Limb profiles: angles from front (0) toward lateral (90), back 180, medial 270.
def limb_prof(front, lateral, back, medial, extra=None):
    spec = {0: front, 90: lateral, 180: back, 270: medial,
            45: 0.5 * (front + lateral) * 1.02, 135: 0.5 * (lateral + back) * 1.02,
            225: 0.5 * (back + medial) * 1.02, 315: 0.5 * (medial + front) * 1.02}
    if extra:
        spec.update(extra)
    return periodic_profile(spec)


# Arm rings: z, centre offset (dlx, df) from humerus/forearm line, radii (front, lateral, back, medial)
ARM_LEVELS = [
    # Neutral hang: palm faces medially, thumb forward. Front = biceps / radial
    # side, back = triceps / ulnar side, lateral = extensors, medial = flexors.
    (1.370, (0.005, 0.000), (0.055, 0.060, 0.061, 0.046)),
    (1.330, (0.003, 0.003), (0.057, 0.056, 0.062, 0.045)),
    (1.285, (0.001, 0.006), (0.062, 0.049, 0.058, 0.046)),
    (1.240, (0.000, 0.006), (0.058, 0.045, 0.051, 0.045)),
    (1.210, (0.000, 0.003), (0.046, 0.042, 0.044, 0.044)),
    (1.190, (0.000, 0.000), (0.042, 0.044, 0.043, 0.046)),
    (1.170, (0.001, 0.003), (0.044, 0.045, 0.041, 0.045)),
    (1.140, (0.002, 0.005), (0.052, 0.049, 0.041, 0.045)),
    (1.100, (0.001, 0.004), (0.050, 0.046, 0.040, 0.043)),
    (1.050, (0.000, 0.002), (0.041, 0.037, 0.035, 0.036)),
    (1.000, (0.000, 0.000), (0.035, 0.028, 0.031, 0.028)),
    (0.960, (0.000, -0.001), (0.031, 0.022, 0.029, 0.021)),
    (0.935, (0.000, -0.002), (0.031, 0.020, 0.029, 0.019)),
]

LEG_LEVELS = [
    # z, centre (lx, f), radii (front, lateral, back, medial), local deltas {angle: +/-m}
    # angles: 0 front, 90 lateral, 180 back, 270 medial.
    (0.800, (0.096, 0.004), (0.092, 0.096, 0.086, 0.078), None),          # tucked under the gluteal fold
    (0.740, (0.096, 0.009), (0.094, 0.091, 0.088, 0.075), None),
    (0.680, (0.095, 0.011), (0.090, 0.085, 0.080, 0.071), None),
    (0.620, (0.094, 0.011), (0.081, 0.075, 0.072, 0.068), {300: 0.004}),
    (0.570, (0.093, 0.009), (0.069, 0.063, 0.062, 0.066), {305: 0.009, 90: -0.002}),   # vastus medialis
    (0.540, (0.092, 0.007), (0.061, 0.055, 0.056, 0.059), {310: 0.004}),
    (0.515, (0.092, 0.006), (0.059, 0.053, 0.052, 0.056), {0: 0.004, 180: -0.003}),   # patella / popliteal
    (0.490, (0.092, 0.004), (0.054, 0.052, 0.055, 0.054), {0: -0.002}),               # patellar tendon
    (0.455, (0.092, -0.001), (0.047, 0.053, 0.063, 0.056), {20: 0.002}),              # tibial tuberosity
    (0.400, (0.092, -0.007), (0.043, 0.058, 0.078, 0.064), {215: 0.006, 150: -0.002}),  # gastrocnemius heads
    (0.340, (0.092, -0.007), (0.041, 0.054, 0.072, 0.059), {220: 0.007, 145: -0.001}),
    (0.270, (0.092, -0.004), (0.036, 0.044, 0.054, 0.045), None),
    (0.200, (0.092, -0.003), (0.032, 0.036, 0.040, 0.035), {180: -0.004}),            # Achilles
    (0.140, (0.092, -0.004), (0.029, 0.032, 0.032, 0.031), {180: -0.004}),
]

# Foot: fan rings about the dorsal ankle crease, then forward sections.
FOOT_PIVOT = (0.092, 0.047, 0.094)          # lx, f, z (dorsal ankle crease)
FOOT_FAN = [
    # theta_deg, centre distance from pivot along -e1, half-length (e1), half-width, lateral shift
    (0.0, 0.040, 0.036, 0.036, 0.000),
    (25.0, 0.048, 0.044, 0.038, 0.000),
    (50.0, 0.055, 0.050, 0.040, 0.001),
    (72.0, 0.052, 0.047, 0.042, 0.002),
    (90.0, 0.046, 0.042, 0.043, 0.002),
]
FOOT_SECTIONS = [
    # f, centre (lx, z), top, bottom, lateral, medial, deltas {angle: m}
    # angles: 0 dorsum, 90 lateral, 180 sole, 270 medial; 225 = medial arch.
    (0.080, (0.093, 0.038), 0.037, 0.038, 0.044, 0.042, {225: -0.009}),
    (0.120, (0.094, 0.031), 0.029, 0.031, 0.048, 0.046, {225: -0.010}),
    (0.155, (0.094, 0.025), 0.023, 0.025, 0.051, 0.049, {225: -0.005}),
    (0.185, (0.094, 0.019), 0.018, 0.019, 0.050, 0.047, None),        # ball of the foot
]
# Toe split ring at the webs (P4-like convention across the foot, medial first):
# R (medial side), D0..D8 dorsal medial->lateral, U (lateral side), P8..P0 plantar.
TOE_SPLIT_F = 0.203
TOE_D_LX = [0.054, 0.066, 0.080, 0.089, 0.098, 0.105, 0.112, 0.124, 0.136]
TOE_SPANS = [(0, 2), (2, 4), (4, 6), (6, 7), (7, 8)]   # big toe .. little toe (D indices)
TOE_TIPS_F = [0.272, 0.268, 0.256, 0.245, 0.233]
TOE_HEIGHT = [0.013, 0.010, 0.0095, 0.009, 0.0085]      # half dorsal-plantar thickness


# --------------------------------------------------------------------------
# Hand (authored in palm frame: a = along +f, d = dorsal = lateral offset)
# --------------------------------------------------------------------------

def hand_point(lx0, a, d, z):
    return (lx0 + d, a, z)


def palm_ring(lx0, z, radial, ulnar, dorsal, palmar, zd=0.0, zp=0.0, thenar=0.0, hypo=0.0, arch=0.15, tilt=0.0):
    """20-vertex palm contour in P4 index convention:
    0 radial, 1..9 dorsal radial->ulnar, 10 ulnar, 11..19 palmar ulnar->radial.
    arch=1 gives an elliptical (wrist-like) section, small values a flat palm.
    tilt lowers the radial side (negative) relative to the ulnar side."""
    def shape(k):
        u = (k - 4) / 4.6
        return 1 - arch * (1 - math.sqrt(max(0.0, 1 - u * u)))
    mid, half = 0.5 * (radial + ulnar), 0.5 * (radial - ulnar)
    zt = lambda a: z + tilt * (a - mid) / half
    inset = 0.004 + 0.010 * arch
    pts = [hand_point(lx0, radial, 0.0, zt(radial))]
    for k in range(9):
        a = radial - inset - (radial - ulnar - 2 * inset) * k / 8
        pts.append(hand_point(lx0, a, dorsal * shape(k), zt(a) + zd))
    pts.append(hand_point(lx0, ulnar, 0.0, zt(ulnar)))
    for k in range(9):
        a = ulnar + inset + (radial - ulnar - 2 * inset) * k / 8
        bulge = hypo * math.exp(-((k - 1.5) / 1.5) ** 2) + thenar * math.exp(-((k - 7.5) / 1.3) ** 2)
        pts.append(hand_point(lx0, a, -(palmar * shape(8 - k) + bulge), zt(a) + zp))
    return pts


FINGERS = ("index", "middle", "ring", "pinky")
FINGER_SIZE = {  # half-width (f), dorsal thickness, palmar thickness at base; tip scale
    "index": (0.0106, 0.0082, 0.0100, 0.80),
    "middle": (0.0108, 0.0084, 0.0103, 0.80),
    "ring": (0.0102, 0.0080, 0.0097, 0.80),
    "pinky": (0.0089, 0.0072, 0.0086, 0.80),
}


# --------------------------------------------------------------------------
# Build
# --------------------------------------------------------------------------

def steer_ring(ring, targets, weight):
    """Slide ring vertices along their own closed contour toward the angular
    positions of `targets` (same index order), keeping the ring's shape/height."""
    if weight <= 0:
        return ring
    R = np.array(ring)
    dense = centripetal_cr(list(R), closed=True, samples=24)
    centre = np.array([0.0, dense[:, 1].mean()])
    d_ang = np.unwrap(np.arctan2(dense[:, 0] - centre[0], dense[:, 1] - centre[1]))
    out = []
    for p, t in zip(R, np.array(targets)):
        theta = math.atan2(t[0] - centre[0], t[1] - centre[1])
        # nearest dense sample by angle (dense angles are monotonic around the ring)
        diff = np.abs((d_ang - theta + math.pi) % (2 * math.pi) - math.pi)
        q = dense[int(np.argmin(diff))]
        s = (1 - weight) * p + weight * np.array([q[0], q[1], p[2]])
        out.append(s)
    out[0][0] = 0.0
    out[16][0] = 0.0
    for i in range(17, 32):  # exact mirror of the left half
        out[i] = mirror(out[32 - i])
    return out


def build_cage(bones):
    B = Builder()

    # ---- shoulder rings (60) and the axilla split ----
    sh = [B.add_many(ring60(r["front"], r["arm"], r["back"]), "shoulder") for r in SHOULDER_RINGS]
    for a, b in zip(sh, sh[1:]):
        B.bridge(a, b)
    A = sh[0]
    cl = B.add_many([to_left(p) for p in AXILLA_CHAIN], "shoulder")
    cr = B.add_many([mirror(to_left(p)) for p in reversed(AXILLA_CHAIN)], "shoulder")  # B_r -> F_r
    torso_top = [A[0]] + A[1:6] + [A[6], cl[0], cl[1], A[23]] + A[24:30] + [A[30]] + A[31:37] + [A[37], cr[0], cr[1], A[54]] + A[55:60]
    assert len(torso_top) == 32

    # ---- torso below axilla (32-rings), columns steered into the axilla folds ----
    top_pts = B.pos(torso_top)
    authored = []
    for level, steer in zip(TORSO_LEVELS, TORSO_COLUMN_STEER):
        z, W, front, back, n, bumps = level[:6]
        n_back = level[6] if len(level) > 6 else None
        ring = ring32_from_half(superellipse_half(z, W, front, back, n=n, bumps=bumps, n_back=n_back))
        authored.append(np.array(steer_ring(ring, top_pts, steer)))
    # Double the vertical loop density (mid-rings between authored levels) so
    # abdominal/back surface definition has enough rows; loops stay continuous.
    dense = []
    for i, ring in enumerate(authored):
        if i:
            dense.append(0.5 * (authored[i - 1] + ring))
        dense.append(ring)
    dense.append(0.5 * (authored[-1] + np.array(top_pts)))
    # Taubin smoothing down each vertex column removes ledges between authored
    # levels without shrinking the chest/glute volumes. The crotch ring (first)
    # and the axilla-adjacent ring (last) stay fixed; symmetry is preserved.
    D = np.array(dense)
    for _ in range(4):
        for lam in (0.5, -0.53):
            D[1:-1] = D[1:-1] + lam * (0.5 * (D[:-2] + D[2:]) - D[1:-1])
    D[:, 0, 0] = 0.0
    D[:, 16, 0] = 0.0
    torso_rings = [B.add_many(list(ring), "torso") for ring in D]
    for a, b in zip(torso_rings, torso_rings[1:]):
        B.bridge(a, b)
    B.bridge(torso_rings[-1], torso_top)
    arm_loop_l = [A[6]] + A[7:23] + [A[23], cl[1], cl[0]]
    arm_loop_r = [A[37]] + A[38:54] + [A[54], cr[1], cr[0]]

    # ---- neck base split + shoulder caps ----
    S3 = sh[-1]
    nl = B.add_many([to_left(p) for p in NECK_SIDE_CHAIN], "shoulder")
    nr = B.add_many([mirror(to_left(p)) for p in reversed(NECK_SIDE_CHAIN)], "shoulder")
    neck_loop = [S3[0]] + S3[1:6] + [S3[6], nl[0], nl[1], S3[23]] + S3[24:30] + [S3[30]] + S3[31:37] + [S3[37], nr[0], nr[1], S3[54]] + S3[55:60]
    cap_l = [S3[6]] + S3[7:23] + [S3[23], nl[1], nl[0]]
    cap_r = [S3[37]] + S3[38:54] + [S3[54], nr[1], nr[0]]
    B.cap(cap_l, a=3, b=7, dome=SHOULDER_CAP_DOME, dome_dir=UP, start=0, region="shoulder")
    B.cap(cap_r, a=3, b=7, dome=SHOULDER_CAP_DOME, dome_dir=UP, start=0, region="shoulder")

    # ---- neck and head (32) ----
    prev = neck_loop
    for control in NECK_RINGS:
        ids = B.add_many(ring32_from_half(control), "neck")
        B.bridge(prev, ids)
        prev = ids
    for control in HEAD_RINGS:
        ids = B.add_many(ring32_from_half(control), "head")
        B.bridge(prev, ids)
        prev = ids
    B.cap(prev, a=8, b=8, dome=CROWN_DOME, dome_dir=UP, start=28, region="head")

    # ---- crotch split ----
    T0 = torso_rings[0]
    cc = B.add_many([to_left(p) for p in CROTCH_CHAIN], "pelvis")  # front -> back
    leg_loop_l = T0[0:17] + [cc[2], cc[1], cc[0]]

    # ---- left limbs, then exact mirror for the right side ----
    centre_count = len(B.v)
    centre_faces = len(B.f)
    build_leg(B, bones, -1, leg_loop_l)
    build_arm(B, bones, -1, arm_loop_l)
    relax_thumb_web(B, bones)
    mirror_left_limbs(B, centre_count, centre_faces)
    del arm_loop_r
    return B


def relax_thumb_web(B, bones, radius=0.022, iterations=4, factor=0.5):
    """Umbrella-relax the cramped thumb/first-web junction of the left hand cage
    (before mirroring) so no quads fold through each other."""
    thumb_mcp = lat(bones, "thumb_02_l", "head")
    index_mcp = lat(bones, "index_01_l", "head")
    centre = np.array([-0.5 * (thumb_mcp[0] + index_mcp[0]), 0.5 * (thumb_mcp[1] + index_mcp[1]),
                       0.5 * (thumb_mcp[2] + index_mcp[2]) + 0.012])
    ids = [i for i in B.regions.get("hand", set()) | B.regions.get("thumb", set())
           if np.linalg.norm(B.v[i] - centre) < radius]
    nbrs = {i: set() for i in ids}
    for f in B.f:
        for k, a in enumerate(f):
            if a in nbrs:
                nbrs[a].update((f[k - 1], f[(k + 1) % len(f)]))
    for _ in range(iterations):
        new = {i: B.v[i] + factor * (np.mean([B.v[j] for j in nbrs[i]], axis=0) - B.v[i]) for i in ids}
        for i, p in new.items():
            B.v[i] = p


def mirror_left_limbs(B, centre_count, centre_faces):
    """Duplicate every vertex/face created for the left limbs as an exact
    mirror; junction vertices map to their mirror partners in the centre."""
    key = lambda p: (round(p[0] * 1e7), round(p[1] * 1e7), round(p[2] * 1e7))
    centre_lookup = {key(B.v[i]): i for i in range(centre_count)}
    mapping = {}
    for i in range(centre_count):
        partner = centre_lookup.get(key(mirror(B.v[i])))
        if partner is not None:
            mapping[i] = partner
    left_count = len(B.v)
    vreg = {}
    for name, ids in B.regions.items():
        for i in ids:
            vreg[i] = name
    for i in range(centre_count, left_count):
        mapping[i] = B.add(mirror(B.v[i]), vreg.get(i))
    for f in list(B.f[centre_faces:]):
        B.f.append(tuple(mapping[i] for i in reversed(f)))


def sidep(side, p):
    """(lx, f, z) -> internal point on the given side (side=-1 left/-X, +1 right)."""
    return np.array([side * p[0], p[1], p[2]], float)


def build_leg(B, bones, side, loop):
    lateral = np.array([float(side), 0.0, 0.0])
    rings = []
    for z, (lx, f), (rf, rl, rb, rm), deltas in LEG_LEVELS:
        # athletic bulk: quads/hamstrings and calves (medial side kept for thigh gap)
        if 0.55 < z < 0.78:  # the top ring stays clear of the v4 rest thumb
            rf, rl, rb = rf * 1.05, rl * 1.05, rb * 1.04
        elif 0.20 < z < 0.46:
            rl, rb, rm = rl * 1.04, rb * 1.05, rm * 1.04
        extra = {}
        if z > 0.70:
            # Flatter anterolateral upper thigh: leaves room for the v4 rest thumb.
            k = (z - 0.70) / 0.10
            extra = {40: 0.5 * (rf + rl) * (1.02 - 0.16 * k), 60: 0.5 * (rf + rl) * (1.02 - 0.15 * k)}
        base = limb_prof(rf, rl, rb, rm, extra)
        for ang, d in (deltas or {}).items():
            extra[ang] = base(math.radians(ang)) + d
        rings.append((sidep(side, (lx, f, z)), FWD, lateral, limb_prof(rf, rl, rb, rm, extra)))
    last = B.loft(loop, rings, region="leg")
    # foot fan about the dorsal ankle crease
    px, pf, pz = FOOT_PIVOT
    fan = []
    for theta, vc, half_len, half_w, shift in FOOT_FAN:
        t = math.radians(theta)
        e1 = np.array([0.0, math.cos(t), math.sin(t)])
        centre = sidep(side, (px + shift, pf, pz)) - e1 * vc
        heel = 1.0 + 0.25 * math.sin(t * 2) if theta < 90 else 1.0
        prof = periodic_profile({0: half_len * 0.55, 45: half_len * 0.75, 90: half_w, 135: half_len * heel * 0.95,
                                 180: half_len * heel, 225: half_len * heel * 0.95, 270: half_w * 0.97,
                                 315: half_len * 0.75})
        fan.append((centre, e1, lateral, prof))
    last = B.loft(last, fan, blend=2, region="foot")
    secs = []
    for f, (lx, zc), top, bottom, lat_r, med_r, deltas in FOOT_SECTIONS:
        spec = {0: top, 45: 0.5 * (top + lat_r) * 1.05, 90: lat_r,
                135: 0.5 * (bottom + lat_r) * 1.08, 180: bottom,
                225: 0.5 * (bottom + med_r) * 1.08, 270: med_r,
                315: 0.5 * (top + med_r) * 1.05}
        for ang, d in (deltas or {}).items():
            spec[ang] = spec.get(ang, periodic_profile(spec)(math.radians(ang))) + d
        secs.append((sidep(side, (lx, f, zc)), UP, lateral, periodic_profile(spec)))
    last = B.loft(last, secs, blend=2, region="foot")
    build_toes(B, side, last)


def build_toes(B, side, section_loop):
    """Split the forefoot at the webs into five toes (8/8/8/6/6-vertex loops)."""
    f0 = TOE_SPLIT_F
    D = [(lx, f0, 0.029 - 0.004 * k / 8) for k, lx in enumerate(TOE_D_LX)]
    P = [(lx, f0 + 0.004, 0.0015) for lx in TOE_D_LX]
    R = (TOE_D_LX[0] - 0.005, f0, 0.015)
    U = (TOE_D_LX[-1] + 0.004, f0, 0.012)
    ring = [R] + D + [U] + list(reversed(P))
    ring_ids = B.add_many([sidep(side, p) for p in ring], "foot")
    # align the lofted forefoot section to this authored ring
    A3, A4 = B.pos(section_loop), B.pos(ring_ids)
    n = len(ring_ids)
    best = None
    for direction in (1, -1):
        for off in range(n):
            idx = [(off + direction * k) % n for k in range(n)]
            cost = float(np.sum(np.linalg.norm(A3[idx] - A4, axis=1)))
            if best is None or cost < best[0]:
                best = (cost, [section_loop[i] for i in idx])
    B.bridge(best[1], ring_ids)
    Rv, Dv, Uv, Pv = ring_ids[0], ring_ids[1:10], ring_ids[10], list(reversed(ring_ids[11:20]))
    webs = {}
    for (_a, b) in TOE_SPANS[:-1]:
        webs[b] = B.add(sidep(side, (TOE_D_LX[b], f0 + 0.010, 0.013)), "foot")
    for t, (a, b) in enumerate(TOE_SPANS):
        top = Dv[a:b + 1]
        bot = Pv[a:b + 1]
        left = Rv if a == 0 else webs[a]
        right = Uv if b == 8 else webs[b]
        loop = [left] + top + [right] + list(reversed(bot))
        # loop runs medial side -> dorsal -> lateral side -> plantar
        lx_c = 0.5 * (TOE_D_LX[a] + TOE_D_LX[b])
        # slightly narrower than the web spacing so neighbouring toes never interpenetrate
        half_w = 0.5 * (TOE_D_LX[b] - TOE_D_LX[a]) + (0.002 if a == 0 else -0.0008)
        h = TOE_HEIGHT[t]
        tip = TOE_TIPS_F[t]
        length = tip - f0
        rings = []
        for frac, s, zc in ((0.22, 1.00, 0.0135), (0.45, 0.96, 0.0125), (0.62, 0.93, 0.0118),
                            (0.80, 0.88, 0.0110), (0.93, 0.70, 0.0100)):
            prof = periodic_profile({0: h * s * 0.95, 90: half_w * s, 180: h * s * 1.05, 270: half_w * s,
                                     45: 0.5 * (h + half_w) * s, 135: 0.5 * (h + half_w) * s * 1.04,
                                     225: 0.5 * (h + half_w) * s * 1.04, 315: 0.5 * (h + half_w) * s})
            rings.append((sidep(side, (lx_c, f0 + length * frac, zc * (h / 0.010))), UP,
                          np.array([float(side), 0.0, 0.0]), prof))
        last = B.loft(loop, rings, blend=2, region="foot")
        if len(loop) == 8:
            B.cap(last, a=2, b=2, dome=0.004, dome_dir=FWD, start=0, region="foot")
        else:
            B.cap(last, a=1, b=2, dome=0.0035, dome_dir=FWD, start=0, region="foot")


def bone_frame(head, tail, ref):
    t = unit(tail - head)
    e1 = unit(ref - np.dot(ref, t) * t)
    e2 = np.cross(t, e1)
    return t, e1, e2


def build_arm(B, bones, side, loop):
    lateral = np.array([float(side), 0.0, 0.0])
    sh = lat(bones, "upperarm_l")
    rings = []
    for z, (dlx, df), (rf, rl, rb, rm) in ARM_LEVELS:
        centre = sidep(side, (sh[0] + dlx, sh[1] + df, z))
        rings.append((centre, FWD, lateral, limb_prof(rf, rl, rb, rm)))
    last = B.loft(loop, rings, region="arm")
    build_hand(B, bones, side, last)


def build_hand(B, bones, side, wrist_loop):
    hand = lat(bones, "hand_l")
    lx0 = hand[0]
    lateral = np.array([float(side), 0.0, 0.0])
    # Wrist ring at the joint, then P1 (thumb split) authored explicitly.
    # Wrist: oval section matching the distal forearm, widening into the palm.
    wrist = palm_ring(lx0 + 0.001, 0.918, 0.003, -0.061, 0.020, 0.019, arch=1.0)
    wrist_ids = B.add_many([sidep(side, p) for p in wrist], "hand")
    B.bridge_aligned(wrist_loop, wrist_ids)
    p0 = palm_ring(lx0 + 0.001, 0.902, 0.016, -0.069, 0.017, 0.020, thenar=0.004, hypo=0.002, arch=0.6)
    p0_ids = B.add_many([sidep(side, p) for p in p0], "hand")
    B.bridge(wrist_ids, p0_ids)
    p1 = palm_ring(lx0 + 0.001, 0.884, 0.031, -0.076, 0.014, 0.020, thenar=0.002, hypo=0.004, arch=0.3)
    p1_ids = B.add_many([sidep(side, p) for p in p1], "hand")
    B.bridge(p0_ids, p1_ids)
    # Thumb-index web chain from dorsal-radial p1[1] to palmar-radial p1[17]:
    # the first web space runs distally toward the index MCP.
    web = [(lx0 + 0.007, 0.030, 0.866), (lx0 - 0.004, 0.035, 0.860), (lx0 - 0.016, 0.029, 0.866)]
    t_ids = B.add_many([sidep(side, p) for p in web], "hand")
    thumb_loop = [p1_ids[17], p1_ids[18], p1_ids[19], p1_ids[0], p1_ids[1]] + t_ids
    palm_loop = p1_ids[1:18] + [t_ids[2], t_ids[1], t_ids[0]]
    # palm rings to the knuckles; radial side lower (distal) below the web
    p2 = palm_ring(lx0 + 0.001, 0.858, 0.022, -0.080, 0.013, 0.018, hypo=0.005, tilt=-0.013)
    p2_ids = B.add_many([sidep(side, p) for p in p2], "hand")
    p2_ids = B.bridge_aligned(palm_loop, p2_ids)
    p3 = palm_ring(lx0 + 0.001, 0.847, 0.022, -0.079, 0.013, 0.016, hypo=0.004, tilt=-0.004)
    p3_raw = B.add_many([sidep(side, p) for p in p3], "hand")
    # p2 was re-indexed for alignment; keep p3 in the same order as p2 by alignment
    p3_ids = B.bridge_aligned(p2_ids, p3_raw)
    # P4 finger split ring (explicit convention) + web chains
    fcent = {name: lat(bones, f"{name}_01_l") for name in FINGERS}
    a_mid = [fcent[n][1] for n in FINGERS]
    webs_a = [0.5 * (a_mid[i] + a_mid[i + 1]) for i in range(3)]
    radial_a = a_mid[0] + 0.012
    ulnar_a = a_mid[3] - 0.011
    dz, pz = 0.840, 0.829
    D = []
    stations = [radial_a - 0.002, a_mid[0], webs_a[0], a_mid[1], webs_a[1], a_mid[2], webs_a[2], a_mid[3], ulnar_a + 0.002]
    for k, a in enumerate(stations):
        knuckle = 0.004 if k % 2 == 1 else 0.0
        D.append(hand_point(lx0, a, 0.0105 + knuckle, dz + (0.002 if k % 2 == 1 else -0.001)))
    P = []
    for k, a in enumerate(stations):
        pad = 0.003 if k % 2 == 1 else 0.0
        P.append(hand_point(lx0, a, -(0.0145 + pad), pz))
    ring4 = [hand_point(lx0, radial_a + 0.002, -0.002, 0.834)] + D + [hand_point(lx0, ulnar_a - 0.002, -0.002, 0.834)] + list(reversed(P))
    p4_raw = B.add_many([sidep(side, p) for p in ring4], "hand")
    # align p3 to p4 convention (p4 order is authoritative for the finger split)
    A3 = B.pos(p3_ids)
    A4 = B.pos(p4_raw)
    best = None
    for direction in (1, -1):
        for off in range(20):
            idx = [(off + direction * k) % 20 for k in range(20)]
            cost = float(np.sum(np.linalg.norm(A3[idx] - A4, axis=1)))
            if best is None or cost < best[0]:
                best = (cost, [p3_ids[i] for i in idx])
    B.bridge(best[1], p4_raw)
    R, Dv, U, Pv = p4_raw[0], p4_raw[1:10], p4_raw[10], list(reversed(p4_raw[11:20]))
    web_ids = []
    for i, a in enumerate(webs_a):
        web_ids.append(B.add(sidep(side, hand_point(lx0, a, -0.001, 0.818)), "hand"))
    W2, W4, W6 = web_ids
    finger_loops = {
        "index": [R, Dv[0], Dv[1], Dv[2], W2, Pv[2], Pv[1], Pv[0]],
        "middle": [Dv[2], Dv[3], Dv[4], W4, Pv[4], Pv[3], Pv[2], W2],
        "ring": [Dv[4], Dv[5], Dv[6], W6, Pv[6], Pv[5], Pv[4], W4],
        "pinky": [Dv[6], Dv[7], Dv[8], U, Pv[8], Pv[7], Pv[6], W6],
    }
    for name in FINGERS:
        build_finger(B, bones, side, name, finger_loops[name])
    build_thumb(B, bones, side, thumb_loop)


def finger_prof(half_w, dors, palm, knuckle=0.0):
    return periodic_profile({0: half_w, 60: 0.5 * (half_w + dors) * 1.04 + knuckle * 0.3,
                             90: dors + knuckle, 120: 0.5 * (half_w + dors) * 1.04 + knuckle * 0.3,
                             180: half_w, 240: 0.5 * (half_w + palm) * 1.06, 270: palm,
                             300: 0.5 * (half_w + palm) * 1.06})


def chain_stations(bones, names, fractions):
    """Points along a chain of bones; fractions are (bone_index, t)."""
    out = []
    for bi, t in fractions:
        h = lat(bones, names[bi], "head")
        tl = lat(bones, names[bi], "tail")
        out.append((h + (tl - h) * t, unit(tl - h)))
    return out


# Finger stations: (bone index, t along bone, width, dorsal, palmar scale, knuckle).
# Palmar creases narrow the palmar side at each joint; dorsal knuckles rise over
# PIP/DIP; the distal phalanx carries a full palmar pad and a flatter nail side.
FINGER_STATIONS = [
    (0, 0.30, 1.00, 1.00, 1.06, 0.0), (0, 0.62, 0.96, 0.96, 1.02, 0.0),
    (0, 0.88, 0.95, 0.97, 0.90, 0.0012),
    (1, 0.00, 0.96, 1.00, 0.88, 0.0022), (1, 0.14, 0.93, 0.95, 0.94, 0.0010),
    (1, 0.50, 0.89, 0.90, 0.98, 0.0), (1, 0.84, 0.87, 0.90, 0.88, 0.0006),
    (2, 0.00, 0.87, 0.92, 0.84, 0.0014), (2, 0.18, 0.85, 0.86, 0.92, 0.0004),
    (2, 0.55, 0.84, 0.78, 1.04, 0.0), (2, 0.86, 0.78, 0.68, 0.96, 0.0),
    (2, 1.02, 0.60, 0.50, 0.70, 0.0),
]


def build_finger(B, bones, side, name, loop):
    names = [f"{name}_01_l", f"{name}_02_l", f"{name}_03_l"]
    hw, dors, palm, _tip = FINGER_SIZE[name]
    rings = []
    for bi, t, sw, sd, sp, knuckle in FINGER_STATIONS:
        (c, tan), = chain_stations(bones, names, [(bi, min(t, 1.0))])
        if t > 1.0:  # beyond the bone tail (fingertip pad)
            h, tl = lat(bones, names[bi], "head"), lat(bones, names[bi], "tail")
            c = h + (tl - h) * t
        c = np.array([side * c[0], c[1], c[2]])
        tan = np.array([side * tan[0], tan[1], tan[2]])
        e1 = unit(FWD - np.dot(FWD, tan) * tan)
        e2 = np.cross(tan, e1)
        if np.dot(e2, np.array([float(side), 0, 0])) < 0:
            e2 = -e2
        rings.append((c, e1, e2, finger_prof(hw * sw, dors * sd, palm * sp, knuckle)))
    last = B.loft(loop, rings, blend=2, region="finger")
    tip_dir = rings[-1][0] - rings[-2][0]
    B.cap(last, a=2, b=2, dome=0.0042, dome_dir=tip_dir, start=0, region="finger")


# Thumb rings after the metacarpal: (bone index, t, (nail, side, pad, side) radii).
THUMB_PHALANX_STATIONS = [
    (1, 0.00, (0.0118, 0.0120, 0.0122, 0.0118)),
    (1, 0.18, (0.0108, 0.0112, 0.0118, 0.0110)),
    (1, 0.55, (0.0100, 0.0106, 0.0114, 0.0104)),
    (1, 0.90, (0.0098, 0.0104, 0.0100, 0.0102)),
    (2, 0.10, (0.0094, 0.0102, 0.0100, 0.0100)),
    (2, 0.50, (0.0082, 0.0098, 0.0112, 0.0096)),
    (2, 0.84, (0.0070, 0.0088, 0.0100, 0.0086)),
    (2, 1.02, (0.0048, 0.0064, 0.0072, 0.0062)),
]


def thumb_prof(r_nail, r_s1, r_pad, r_s2):
    return periodic_profile({0: r_nail, 90: r_s1, 180: r_pad, 270: r_s2,
                             45: 0.5 * (r_nail + r_s1) * 1.03, 135: 0.5 * (r_s1 + r_pad) * 1.05,
                             225: 0.5 * (r_pad + r_s2) * 1.05, 315: 0.5 * (r_s2 + r_nail) * 1.03})


def build_thumb(B, bones, side, loop):
    names = ["thumb_01_l", "thumb_02_l", "thumb_03_l"]
    flip = lambda p: np.array([side * p[0], p[1], p[2]])
    # Nail faces anterolaterally in the neutral hang.
    nail_ref = unit(np.array([0.55 * side, 0.83, 0.0]))

    def frame(tan):
        e1 = unit(nail_ref - np.dot(nail_ref, tan) * tan)
        return e1, np.cross(tan, e1)

    # Thenar/metacarpal rings grow out of the base loop toward the MCP joint
    # (the CMC joint itself lies buried inside the thenar eminence).
    loop_pts = B.pos(loop)
    centroid = loop_pts.mean(axis=0)
    mcp = flip(lat(bones, "thumb_02_l", "head"))
    to_mcp = mcp - centroid
    rings = []
    # shifted radially (+f) so the thenar pad sits beside the palm, not inside it
    for frac, r, shift in ((0.36, (0.0162, 0.0178, 0.0215, 0.0178), 0.0025),
                           (0.68, (0.0134, 0.0145, 0.0168, 0.0142), 0.0010)):
        tan = unit(to_mcp)
        e1, e2 = frame(tan)
        rings.append((centroid + to_mcp * frac + FWD * shift, e1, e2, thumb_prof(*r)))
    for bi, t, r in THUMB_PHALANX_STATIONS:
        h, tl = lat(bones, names[bi], "head"), lat(bones, names[bi], "tail")
        c = flip(h + (tl - h) * t)
        tan = unit(flip(tl - h))
        e1, e2 = frame(tan)
        rings.append((c, e1, e2, thumb_prof(*r)))
    last = B.loft(loop, rings, blend=2, region="thumb")
    tip_dir = rings[-1][0] - rings[-2][0]
    B.cap(last, a=2, b=2, dome=0.0045, dome_dir=tip_dir, start=0, region="thumb")


# --------------------------------------------------------------------------
# Catmull-Clark (plain Python, closed manifold quad meshes)
# --------------------------------------------------------------------------

def catmull_clark(V, F, regions=None):
    V = np.asarray(V, float)
    nv = len(V)
    fp = np.array([V[list(f)].mean(axis=0) for f in F])
    edge_faces: dict[tuple[int, int], list[int]] = {}
    for fi, f in enumerate(F):
        for a, b in zip(f, f[1:] + f[:1]):
            edge_faces.setdefault((min(a, b), max(a, b)), []).append(fi)
    edges = list(edge_faces)
    eindex = {e: i for i, e in enumerate(edges)}
    ep = np.zeros((len(edges), 3))
    for i, (a, b) in enumerate(edges):
        fs = edge_faces[(a, b)]
        if len(fs) != 2:
            raise ValueError(f"Non-manifold edge {(a, b)} with {len(fs)} faces")
        ep[i] = (V[a] + V[b] + fp[fs[0]] + fp[fs[1]]) / 4
    vf = [[] for _ in range(nv)]
    ve = [[] for _ in range(nv)]
    for fi, f in enumerate(F):
        for a in f:
            vf[a].append(fi)
    for (a, b) in edges:
        ve[a].append((a, b))
        ve[b].append((a, b))
    newV = np.zeros((nv, 3))
    for i in range(nv):
        n = len(vf[i])
        Fa = fp[vf[i]].mean(axis=0)
        Ra = np.mean([(V[a] + V[b]) / 2 for a, b in ve[i]], axis=0)
        newV[i] = (Fa + 2 * Ra + (n - 3) * V[i]) / n
    out_v = np.concatenate([newV, ep, fp])
    e_off, f_off = nv, nv + len(edges)
    out_f = []
    for fi, f in enumerate(F):
        k = len(f)
        for j in range(k):
            a, b, prev = f[j], f[(j + 1) % k], f[j - 1]
            out_f.append((a, e_off + eindex[(min(a, b), max(a, b))], f_off + fi,
                          e_off + eindex[(min(prev, a), max(prev, a))]))
    new_regions = None
    if regions is not None:
        new_regions = {}
        vreg = {}
        for name, ids in regions.items():
            for i in ids:
                vreg[i] = name
        for name, ids in regions.items():
            s = set(ids)
            for i, (a, b) in enumerate(edges):
                if vreg.get(a) == name or vreg.get(b) == name:
                    s.add(e_off + i)
            for fi, f in enumerate(F):
                if any(vreg.get(x) == name for x in f):
                    s.add(f_off + fi)
            new_regions[name] = s
    return out_v, out_f, new_regions


# --------------------------------------------------------------------------
# Surface muscle definition (authored displacement field, applied after
# subdivision along vertex normals). Left side authored as (lx, f, z); the right
# side is the exact mirror. Each entry is limited to named generator regions.
#   ("bump", regions, centre, radii (lx, f, z), amplitude)
#   ("line", regions, p0, p1, radius, amplitude)   # ridge (+) / groove (-)
# --------------------------------------------------------------------------

TORSO = ("torso", "shoulder", "pelvis")
DETAIL_GAIN = 1.0  # global multiplier on every amplitude below
MUSCLE_DETAIL = [
    # --- chest ---
    ("bump", TORSO, (0.068, 0.128, 1.362), (0.050, 0.040, 0.034), 0.005),     # pectoralis major mass
    ("line", TORSO, (0.018, 0.122, 1.308), (0.120, 0.096, 1.335), 0.010, -0.003),  # lower pec border
    ("line", TORSO, (0.000, 0.126, 1.415), (0.000, 0.120, 1.315), 0.009, -0.003),  # sternal groove
    ("line", TORSO, (0.138, 0.074, 1.462), (0.160, 0.046, 1.405), 0.007, -0.002),  # deltopectoral groove
    # --- abdomen ---
    ("line", TORSO, (0.000, 0.113, 1.300), (0.000, 0.104, 1.040), 0.007, -0.0045),  # linea alba
    ("line", TORSO, (0.004, 0.112, 1.245), (0.056, 0.108, 1.238), 0.0055, -0.0040),  # tendinous intersections
    ("line", TORSO, (0.004, 0.109, 1.182), (0.058, 0.105, 1.176), 0.0055, -0.0040),
    ("line", TORSO, (0.004, 0.106, 1.118), (0.058, 0.103, 1.114), 0.0055, -0.0032),
    ("bump", TORSO, (0.030, 0.112, 1.272), (0.022, 0.015, 0.024), 0.0050),       # rectus pads
    ("bump", TORSO, (0.031, 0.109, 1.211), (0.023, 0.015, 0.026), 0.0055),
    ("bump", TORSO, (0.031, 0.106, 1.148), (0.023, 0.015, 0.026), 0.0050),
    ("bump", TORSO, (0.029, 0.104, 1.080), (0.022, 0.015, 0.030), 0.0040),
    ("line", TORSO, (0.068, 0.104, 1.290), (0.060, 0.098, 1.040), 0.008, -0.0040),  # linea semilunaris
    ("bump", TORSO, (0.112, 0.064, 1.080), (0.030, 0.030, 0.055), 0.006),         # external oblique
    ("line", TORSO, (0.112, 0.082, 1.000), (0.052, 0.090, 0.925), 0.012, -0.0030),  # inguinal "V" line
    ("bump", TORSO, (0.136, 0.064, 1.272), (0.012, 0.012, 0.010), 0.0030),        # serratus digitations
    ("bump", TORSO, (0.142, 0.054, 1.240), (0.012, 0.012, 0.010), 0.0030),
    ("bump", TORSO, (0.144, 0.042, 1.208), (0.012, 0.012, 0.010), 0.0026),
    # --- back ---
    ("bump", TORSO, (0.074, -0.070, 1.565), (0.046, 0.036, 0.040), 0.008),       # upper trapezius
    ("bump", TORSO, (0.050, -0.140, 1.460), (0.040, 0.020, 0.050), 0.005),       # middle trapezius / rhomboid
    ("bump", TORSO, (0.088, -0.160, 1.420), (0.034, 0.020, 0.034), 0.008),       # infraspinatus
    ("line", TORSO, (0.045, -0.150, 1.470), (0.080, -0.155, 1.320), 0.008, -0.004),  # medial scapular border
    ("bump", TORSO, (0.140, -0.120, 1.370), (0.022, 0.024, 0.030), 0.006),       # teres major
    ("bump", TORSO, (0.130, -0.112, 1.290), (0.030, 0.040, 0.075), 0.009),       # latissimus
    ("line", TORSO, (0.100, -0.140, 1.200), (0.150, -0.060, 1.330), 0.010, -0.002),  # lat lower edge
    ("line", TORSO, (0.030, -0.100, 1.200), (0.030, -0.086, 0.990), 0.015, 0.007),  # erector spinae
    # --- glutes / hips ---
    ("bump", TORSO, (0.086, -0.132, 0.925), (0.050, 0.040, 0.050), 0.004),       # gluteus maximus
    ("bump", TORSO, (0.160, -0.020, 0.950), (0.018, 0.020, 0.020), -0.003),      # hip dimple
    # --- arms ---
    ("bump", ("arm", "shoulder"), (0.205, 0.030, 1.450), (0.026, 0.020, 0.034), 0.005),   # anterior deltoid
    ("bump", ("arm", "shoulder"), (0.282, -0.030, 1.448), (0.020, 0.030, 0.040), 0.006),  # lateral deltoid
    ("bump", ("arm", "shoulder"), (0.235, -0.104, 1.440), (0.026, 0.020, 0.034), 0.005),  # posterior deltoid
    ("line", ("arm",), (0.272, -0.030, 1.345), (0.240, 0.020, 1.320), 0.007, -0.002),     # deltoid insertion edge
    ("bump", ("arm",), (0.215, 0.036, 1.268), (0.024, 0.018, 0.060), 0.006),     # biceps
    ("bump", ("arm",), (0.218, -0.092, 1.320), (0.028, 0.020, 0.060), 0.006),    # triceps long/lateral head
    ("line", ("arm",), (0.265, -0.030, 1.360), (0.260, -0.020, 1.220), 0.008, -0.003),  # biceps/triceps groove
    ("bump", ("arm",), (0.232, 0.034, 1.128), (0.020, 0.020, 0.050), 0.004),     # brachioradialis
    ("bump", ("arm",), (0.238, -0.025, 1.110), (0.016, 0.018, 0.050), 0.003),    # wrist extensors
    # --- legs ---
    ("line", ("leg",), (0.095, 0.100, 0.800), (0.093, 0.080, 0.610), 0.020, 0.005),   # rectus femoris
    ("bump", ("leg",), (0.178, 0.000, 0.700), (0.020, 0.040, 0.100), 0.006),     # vastus lateralis sweep
    ("bump", ("leg",), (0.055, 0.042, 0.585), (0.024, 0.026, 0.034), 0.007),     # vastus medialis teardrop
    ("line", ("leg",), (0.188, -0.010, 0.790), (0.146, -0.006, 0.560), 0.008, -0.003),  # iliotibial band
    ("line", ("leg",), (0.094, -0.094, 0.780), (0.094, -0.066, 0.560), 0.007, -0.003),  # hamstring split
    ("line", ("leg",), (0.030, 0.050, 0.800), (0.075, 0.075, 0.600), 0.008, -0.002),  # sartorius line
    ("bump", ("leg",), (0.070, -0.078, 0.400), (0.024, 0.020, 0.060), 0.006),    # gastrocnemius medial
    ("bump", ("leg",), (0.120, -0.072, 0.420), (0.020, 0.020, 0.050), 0.005),    # gastrocnemius lateral
    ("line", ("leg",), (0.130, 0.020, 0.420), (0.110, 0.030, 0.200), 0.010, 0.002),   # tibialis anterior
]


def vertex_normals(V, F):
    N = np.zeros_like(V)
    for f in F:
        p = V[list(f)]
        n = np.cross(p[2] - p[0], p[3] - p[1]) if len(f) == 4 else np.cross(p[1] - p[0], p[2] - p[0])
        for i in f:
            N[i] += n
    L = np.linalg.norm(N, axis=1)
    L[L == 0] = 1
    return N / L[:, None]


def apply_muscle_detail(V, F, regions):
    """Displace along outward normals by the authored MUSCLE_DETAIL field."""
    V = np.array(V, float)
    N = vertex_normals(V, orient_faces(V, F))  # consistently outward in these coordinates
    disp = np.zeros(len(V))
    for entry in MUSCLE_DETAIL:
        kind, names = entry[0], entry[1]
        ids = sorted(set().union(*(set(regions.get(n, ())) for n in names)))
        if not ids:
            continue
        P = V[ids]
        total = np.zeros(len(ids))
        for sgn in (-1.0, 1.0):  # left (-X) authored, right mirrored
            if kind == "bump":
                c, r, amp = np.array(entry[2], float), np.array(entry[3], float), entry[4]
                c = np.array([sgn * c[0], c[1], c[2]])
                q = (P - c) / r
                total += DETAIL_GAIN * amp * np.exp(-np.sum(q * q, axis=1))
            else:
                p0, p1, rad, amp = np.array(entry[2], float), np.array(entry[3], float), entry[4], entry[5]
                p0 = np.array([sgn * p0[0], p0[1], p0[2]])
                p1 = np.array([sgn * p1[0], p1[1], p1[2]])
                seg = p1 - p0
                t = np.clip(((P - p0) @ seg) / (seg @ seg), 0.0, 1.0)
                d = np.linalg.norm(P - (p0 + t[:, None] * seg), axis=1)
                total += DETAIL_GAIN * amp * np.exp(-(d / rad) ** 2)
        disp[ids] += total
    return V + N * disp[:, None]


# --------------------------------------------------------------------------
# Finishing: exact height, grounded soles, exact symmetry
# --------------------------------------------------------------------------

def smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def finish(V):
    V = np.array(V, float)
    z = V[:, 2]
    zmin = z.min()
    lo = 0.25
    V[:, 2] -= zmin * (1 - smoothstep((z - zmin) / (lo - zmin)))
    z = V[:, 2]
    zmax = z.max()
    hi = 1.60
    V[:, 2] += (TARGET_HEIGHT - zmax) * smoothstep((z - hi) / (zmax - hi))
    V[np.abs(V[:, 2]) < 1e-9, 2] = 0.0
    # ground the plantar surface of heel/ball/toes
    V[V[:, 2] < 0.0025, 2] = 0.0
    return V


def enforce_symmetry(V, tol=1e-6):
    """Average each vertex with its mirror partner (construction is symmetric;
    this removes floating-point drift). Midline vertices get x = 0."""
    V = np.array(V, float)
    keys = {}
    for i, p in enumerate(V):
        keys.setdefault((round(p[0] / tol), round(p[1] / tol), round(p[2] / tol)), []).append(i)
    for i, p in enumerate(V):
        if abs(p[0]) < tol:
            V[i, 0] = 0.0
    return V


def orient_faces(V, F):
    """Make winding consistent across the closed surface, then outward."""
    V = np.asarray(V, float)
    F = [list(f) for f in F]
    edge_faces = {}
    for fi, f in enumerate(F):
        for a, b in zip(f, f[1:] + f[:1]):
            edge_faces.setdefault((min(a, b), max(a, b)), []).append(fi)
    seen = [False] * len(F)
    for seed in range(len(F)):
        if seen[seed]:
            continue
        seen[seed] = True
        stack = [seed]
        while stack:
            fi = stack.pop()
            f = F[fi]
            directed = set(zip(f, f[1:] + f[:1]))
            for a, b in directed:
                for gj in edge_faces[(min(a, b), max(a, b))]:
                    if gj == fi or seen[gj]:
                        continue
                    g = F[gj]
                    if (a, b) in set(zip(g, g[1:] + g[:1])):
                        F[gj] = list(reversed(g))
                    seen[gj] = True
                    stack.append(gj)
    # signed volume: positive when faces point outward
    vol = 0.0
    for f in F:
        p0 = V[f[0]]
        for i in range(1, len(f) - 1):
            vol += np.dot(p0, np.cross(V[f[i]], V[f[i + 1]])) / 6
    if vol < 0:
        F = [list(reversed(f)) for f in F]
    return [tuple(f) for f in F]


def min_distance(A, B, chunk=512):
    A, B = np.asarray(A, float), np.asarray(B, float)
    if len(A) == 0 or len(B) == 0:
        return None
    best = np.inf
    for i in range(0, len(A), chunk):
        d = np.linalg.norm(A[i:i + chunk, None, :] - B[None, :, :], axis=2)
        best = min(best, float(d.min()))
    return best


def neutral_clearance(result):
    """Vertex-sampled rest-pose gaps (metres) between parts that must not touch.
    Left side only (the body is mirror-symmetric)."""
    V = result["vertices"]
    reg = result["regions"]
    left = V[:, 0] < 0
    def sel(names, zmax=None):
        ids = sorted(set().union(*(set(reg.get(n, [])) for n in names)))
        P = V[ids]
        m = P[:, 0] < 0
        if zmax is not None:
            m &= P[:, 2] < zmax
        return P[m]
    hand = sel(["hand", "finger", "thumb"])
    arm_low = sel(["arm"], zmax=1.28)
    body = sel(["leg", "torso", "pelvis"])
    del left
    return {
        "hand_to_body_m": round(min_distance(hand, body), 4),
        "arm_below_axilla_to_body_m": round(min_distance(arm_low, body), 4),
    }


def to_blender(V):
    V = np.asarray(V, float)
    return np.stack([V[:, 0], -V[:, 1], V[:, 2]], axis=1)


def build(rig_path: Path = RIG_PAYLOAD, subdivide: bool = True):
    bones = load_rig(rig_path)
    B = build_cage(bones)
    V, F, regions = np.array(B.v), [tuple(f) for f in B.f], B.regions
    cage = {"vertices": len(V), "faces": len(F)}
    if subdivide:
        V, F, regions = catmull_clark(V, F, regions)
        V = apply_muscle_detail(V, F, regions)
    V = enforce_symmetry(finish(V))
    Vb = to_blender(V)
    F = orient_faces(Vb, F)
    return {
        "vertices": Vb,
        "faces": F,
        "regions": {k: sorted(v) for k, v in (regions or {}).items()},
        "cage": cage,
        "generator_version": GENERATOR_VERSION,
        "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "rig_payload_sha256": hashlib.sha256(Path(rig_path).read_bytes()).hexdigest(),
    }


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from original_o2_mesh_checks import inspect_mesh
    result = build()
    V = result["vertices"]
    report = inspect_mesh([tuple(p) for p in V], [tuple(f) for f in result["faces"]])
    report["cage"] = result["cage"]
    print(json.dumps(report, indent=2))
