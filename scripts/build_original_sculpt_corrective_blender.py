#!/usr/bin/env python3
"""S4: procedural "sculpt" corrective keys for the overhead press (review-only; bpy).  R10 (Claude, 14 Oct 2026).

Owner, comparing the press with a reference photo series: "Yes, start with A then do B" (B = corrective shapes for the
deltoid cap and the armpit at the press stages, judged against the photo).  The photo shows, and R9 lacks:
  * a full, round deltoid cap at every stage (the deltoid is contracted while pressing);
  * a deep armpit hollow between the chest (pectoral) fold and the back (latissimus) fold near the top and at lockout;
  * the upper trapezius bunching beside the neck at lockout (the shrug);
and R9 + the full-range press has a crease of inner-arm skin folding onto itself in the armpit at lockout.

Per key (press-path pose at the key elevation, scripts/original_v1_press_extension.py; all review drives on) and side, in
posed space:
  1. unfold: vertices of self-intersecting faces (+ UNFOLD_RINGS rings) get UNFOLD_ITERS Laplacian passes;
  2. sculpt: three smooth bumps along the posed vertex normals, each a cosine falloff around a rest-space centre (relative
     to the side's glenohumeral pivot): deltoid (outward), armpit vault (inward), upper trapezius (outward), with per-key
     depths (DEPTHS);
  3. the posed offset is mapped to rest through the blended LBS matrices (damped) and capped;
then a count-based guard over the press path: where a key adds self-intersecting pairs or collapsed faces, the deltas of the
offending vertices (+ 2 rings) are halved.  Keys HGPT_S4_SCULPT_<s>_<ht>, driven by drives.drive_s1 on elevation (family
start START_DEG); the last key holds above its elevation.
"""
from __future__ import annotations

import math
import os
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

import build_original_movement_benchmarks_blender as bench  # noqa: E402
import original_v1_review_candidate_drives as drives  # noqa: E402
import original_v1_press_extension as px  # noqa: E402

_E = os.environ
PREFIX = "HGPT_S4_SCULPT_"
KEYS_HT = tuple(float(v) for v in _E.get("S4_KEYS", "85,110,145,172").split(","))
START_DEG = 60.0
# region centres relative to the GH pivot (m; x is lateral (+) / medial (-) for the side, y anterior (-) / posterior (+))
# and radii; per-key depths in m (+ outward, - inward)
REGIONS = {
    "deltoid": {"centre": (0.035, 0.0, 0.0), "radius": float(_E.get("S4_DELT_R", 0.10))},
    "armpit": {"centre": (-0.05, 0.02, -0.075), "radius": float(_E.get("S4_AX_R", 0.07))},
    "trapezius": {"centre": (-0.10, 0.03, 0.07), "radius": float(_E.get("S4_TRAP_R", 0.07))},
}
DEPTHS = {   # key elevation -> region -> depth (m)
    85.0: {"deltoid": 0.010, "armpit": 0.0, "trapezius": 0.0},
    110.0: {"deltoid": 0.012, "armpit": -0.004, "trapezius": 0.0},
    145.0: {"deltoid": 0.012, "armpit": -0.012, "trapezius": 0.004},
    172.0: {"deltoid": 0.010, "armpit": -0.018, "trapezius": 0.010},
}
_scale = float(_E.get("S4_SCALE", 1.0))
REGION_SCALE = {k: float(v) for k, v in (x.split(":") for x in _E.get("S4_REGION_SCALE", "deltoid:1,armpit:1,trapezius:1").split(","))}
UNFOLD_ITERS = int(_E.get("S4_UNFOLD", 30))
UNFOLD_RINGS = 3
DAMP = 0.05
CAP_M = 0.04
SIDES = ("l", "r")


def press_pose(result, ht):
    """The full-press path pose at elevation ht (inverse of press_state's smoothstep)."""
    k = (ht - px.START_HT) / (px.LOCKOUT_HT - px.START_HT)
    lo, hi = 0.0, 1.0
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if px._smooth(mid) < k:
            lo = mid
        else:
            hi = mid
    return px.pose_press_full(result, 0.5 * (lo + hi))


def _bump(d, r):
    return 0.5 * (1 + math.cos(math.pi * d / r)) if d < r else 0.0


def _normals(V, F):
    N = np.zeros_like(V)
    for f in F:
        a, b, c = V[f[0]], V[f[1]], V[f[2]]
        n = np.cross(b - a, c - a)
        for i in f:
            N[i] += n
    L = np.linalg.norm(N, axis=1)
    L[L < 1e-12] = 1.0
    return N / L[:, None]


def build(result):
    body, rig = result["body"], result["runtime"]
    names = {g.index: g.name for g in body.vertex_groups}
    deform = [b.name for b in rig.data.bones if b.use_deform]
    W = [{names[g.group]: g.weight for g in v.groups if names[g.group] in deform and g.weight > 0} for v in body.data.vertices]
    adj = [set() for _ in body.data.vertices]
    for e in body.data.edges:
        a, b = e.vertices
        adj[a].add(b); adj[b].add(a)
    rest = body.data.vertices
    R0 = np.array([tuple(v.co) for v in rest])
    weights = {}
    for s in SIDES:
        sign = 1.0 if s == "r" else -1.0
        piv = np.array(tuple(rig.data.bones[f"upperarm_{s}"].head_local))
        side_mask = R0[:, 0] * sign > 0.03
        weights[s] = {}
        for reg, spec in REGIONS.items():
            c = piv + np.array((spec["centre"][0] * sign, spec["centre"][1], spec["centre"][2]))
            d = np.linalg.norm(R0 - c, axis=1)
            w = np.array([_bump(x, spec["radius"]) for x in d]) * side_mask
            weights[s][reg] = w
    log, angles = {}, {s: [] for s in SIDES}
    for ht in KEYS_HT:
        bench._reset(rig)
        for kb in body.data.shape_keys.key_blocks[1:]:
            kb.value = 0.0
        press_pose(result, ht)
        drives.drive(rig, body)
        for kb in body.data.shape_keys.key_blocks:
            if kb.name.startswith(PREFIX):
                kb.value = 0.0
        bpy.context.view_layer.update()
        Vl, F = bench._evaluated(body)
        P = np.array([tuple(v) for v in Vl])
        N = _normals(P, F)
        tree = BVHTree.FromPolygons(Vl, F, all_triangles=True)
        fs = [set(f) for f in F]
        folded = {v for a, b in tree.overlap(tree) if a < b and not (fs[a] & fs[b]) for f in (a, b) for v in F[f]}
        mats = {n: np.array((rig.pose.bones[n].matrix @ rig.data.bones[n].matrix_local.inverted()).to_3x3()) for n in deform}
        entry = {}
        for s in SIDES:
            angles[s].append(drives.elevation_deg(rig, s))
            sign = 1.0 if s == "r" else -1.0
            kb = body.shape_key_add(name=f"{PREFIX}{s}_{int(round(ht))}", from_mix=False)
            kb.value = 0.0
            Q = P.copy()
            zone = {i for i in folded if R0[i, 0] * sign > 0.03}
            for _ in range(UNFOLD_RINGS):
                zone |= {j for i in zone for j in adj[i] if R0[j, 0] * sign > 0.03}
            for _ in range(UNFOLD_ITERS):
                new = {i: Q[i] + 0.5 * (sum(Q[j] for j in adj[i]) / len(adj[i]) - Q[i]) for i in zone}
                for i, p in new.items():
                    Q[i] = p
            offset = Q - P
            for reg, depth in DEPTHS[min(DEPTHS, key=lambda h: abs(h - ht))].items():
                offset += (depth * _scale * REGION_SCALE.get(reg, 1.0)) * weights[s][reg][:, None] * N
            moved = np.where(np.linalg.norm(offset, axis=1) > 1e-6)[0]
            clipped, maxp = 0, 0.0
            for i in moved:
                dv = offset[i]
                maxp = max(maxp, float(np.linalg.norm(dv)))
                A = sum(x * mats[nm] for nm, x in W[i].items())
                U, sv, Vt = np.linalg.svd(A)
                dr = Vt.T @ np.diag(sv / (sv ** 2 + DAMP ** 2)) @ U.T @ dv
                L = float(np.linalg.norm(dr))
                if L > CAP_M:
                    dr *= CAP_M / L; clipped += 1
                kb.data[i].co = rest[i].co + Vector(dr)
            entry[s] = {"moved": int(len(moved)), "unfold_zone": len(zone), "max_posed_mm": round(maxp * 1000, 1),
                        "clipped": clipped, "elevation_deg": round(angles[s][-1], 2)}
        log[str(ht)] = entry
    for s in SIDES:
        rig[f"hgpt_s4_angles_{s}"] = list(angles[s])
    log["guard"] = _guard(result, adj)
    bench._reset(rig)
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    return log


def _guard(result, adj, rounds=8, rings=2, ts=tuple(i / 20 for i in range(21))):
    body, rig = result["body"], result["runtime"]
    keys = [kb for kb in body.data.shape_keys.key_blocks if kb.name.startswith(PREFIX)]
    rest = body.data.vertices
    bench._reset(rig)
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    V0, F = bench._evaluated(body)
    A0 = [bench._area(V0, f) for f in F]
    fs = [set(f) for f in F]
    key = lambda v, sx: (round(sx * v.co.x, 5), round(v.co.y, 5), round(v.co.z, 5))
    by_pos = {key(v, 1.0): v.index for v in rest}
    mirror = {v.index: by_pos[key(v, -1.0)] for v in rest if key(v, -1.0) in by_pos}

    def bad():
        V, _ = bench._evaluated(body)
        tree = BVHTree.FromPolygons(V, F, all_triangles=True)
        return ({(a, b) for a, b in tree.overlap(tree) if a < b and not (fs[a] & fs[b])},
                {k for k, f in enumerate(F) if A0[k] > 1e-12 and bench._area(V, f) / A0[k] < 0.1})
    hist = []
    for _pass in range(3):
        passlog = {}
        for t in ts:
            px.pose_press_full(result, t)
            drives.drive(rig, body)
            vals = {kb.name: kb.value for kb in keys}
            active = [kb for kb in keys if kb.value > 0]
            if not active:
                continue
            for kb in keys:
                kb.value = 0.0
            base_p, base_c = bad()
            h = []
            for _ in range(rounds):
                for kb in keys:
                    kb.value = vals[kb.name]
                p, c = bad()
                h.append((len(p) - len(base_p), len(c) - len(base_c)))
                if len(p) <= len(base_p) and len(c) <= len(base_c):
                    break
                hit = set()
                if len(p) > len(base_p):
                    hit |= {v for a, b in p - base_p for f in (a, b) for v in F[f]}
                if len(c) > len(base_c):
                    hit |= {v for f in c - base_c for v in F[f]}
                for _r in range(rings):
                    hit |= {j for i in hit for j in adj[i]}
                hit |= {mirror[i] for i in hit if i in mirror}           # symmetric: both sides back off
                for kb in active:
                    for i in hit:
                        kb.data[i].co = rest[i].co + (kb.data[i].co - rest[i].co) * 0.5
            passlog[f"{t:.2f}"] = h
            for kb in keys:
                kb.value = 0.0
        hist.append(passlog)
        if all(len(x) == 1 for x in passlog.values()):
            break
    bench._reset(rig)
    return {"extra_pairs_and_collapsed_per_round": hist}
