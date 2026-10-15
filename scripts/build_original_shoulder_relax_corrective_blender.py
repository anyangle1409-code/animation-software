#!/usr/bin/env python3
"""S1: overhead shoulder relax corrective on top of R1 (W3A helper + reference drive), review-only diagnostic (bpy).

R1's W3A helper removes the a003 axillary collapse/tear at full press but leaves ~230 more faces stretched > x2 at 160 deg
(upper-arm-dominant skin carrying partial helper weight: the gradient between the half-rotation helper and the
full-rotation arm).  A parameter sweep (transfer, fraction, smoothing, taper) only trades that stretch against collapse and
volume loss, so it is structural.  S1 tries a pose-space corrective instead (no extra joints; K1-style driven morphs):

  per key elevation KEYS_HT and side, in the coupled pose with the R1 drives active:
    1. region: the W3A helper zone of that side (z > ZONE_Z, |x| > ZONE_X, upper-arm/girdle/helper weighted); every
       other vertex is fixed;
    2. tangential pull-only spring relaxation: each free vertex moves toward the mean of the positions its neighbours ask
       for, where only edges longer than at REST are shortened (to rest length) and shorter edges are left as they are;
       moves are projected onto the posed tangent plane (skin slides, it does not inflate); RELAX_ITERS iterations, step
       RELAX_STEP; the fixed boundary makes the displacement vanish at the zone edge (no seam);
    3. the posed displacement is mapped to rest space through each vertex's blended LBS matrix with Tikhonov damping
       DAMP (shoulder matrices are near-singular: W2 sigma_min 0.0024), capped at DELTA_CAP_M, then smoothed over
       DELTA_SMOOTH Laplacian passes (zero outside the zone; without it the key leaves faceted, lumpy skin: rejected);
    4. volume: a rest-normal offset tapered to 0 at the zone edge gives each key pair zero volume change at its pose;
    5. collision guard over the driven range (every 5 deg, 95-160, interpolated key values): zone vertices in NEW
       intersecting or collapsed faces (+ 2 rings, + their mirror vertices so both sides stay symmetric) have their delta
       halved in the active keys until no checked pose adds a pair or a collapsed face.
  Keys HGPT_S1_SHOULDER_<s>_<ht> are driven per side by the measured humerothoracic elevation (angle between the upper
  arm and the thorax's downward axis) with piecewise-linear hats from ACTIVATION_START
  (scripts/original_v1_review_candidate_drives.py drive_s1).
Measured: coupled sweep 0-160 (collapse / stretch > 2 / pairs / volume) R1 vs R1+S1.  With --out the keys are saved into a
separate review blend R2 (R1 + S1, still a 67-bone file); nothing is approved.

  python3.13 build_original_shoulder_relax_corrective_blender.py -- --blend R1.blend [--report JSON] [--out R2.blend]
  R6: S1_ZONE=stretch S1_SRINGS=20 S1_SRATIO=1.2 S1_ITERS=1000 ... -- --blend R5.blend --out R6.blend --name R6 --report JSON
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

import build_original_movement_benchmarks_blender as bench  # noqa: E402
import original_v1_review_candidate_drives as drives  # noqa: E402

import os as _os
KEYS_HT = tuple(int(v) for v in _os.environ.get("S1_KEYS", "120,145,160").split(","))          # coupled HT elevations at which keys are solved
ACTIVATION_START = drives.S1_START  # measured elevation (deg) below which every key is 0
ZERO_KEYS = tuple(int(v) for v in _os.environ.get("S1_ZEROKEYS", "").split(",") if v)   # empty closing keys (R7 fold)
RELAX_ITERS = int(_os.environ.get("S1_ITERS", 150))
RELAX_STEP = 0.5
RELAX_MODE = _os.environ.get("S1_MODE", "pull")     # "pull": only shorten stretched edges (selected); "spring": both ways (rejected:
#                                                      slides skin into the axilla, pairs 110 -> 494 at 160 deg)
DAMP = float(_os.environ.get("S1_DAMP", 0.05))
DELTA_CAP_M = float(_os.environ.get("S1_CAP", 0.030))
DELTA_SMOOTH = int(_os.environ.get("S1_DSMOOTH", 20))   # Laplacian passes over the rest-space key deltas
VOLUME_RESTORE = _os.environ.get("S1_VOLUME", "1") == "1"   # zero volume change per key at its pose
BACKOFF = _os.environ.get("S1_BACKOFF", "1") == "1"   # collision guard at each key pose
SCORE_C = float(_os.environ.get("S1_SCOREC", 10))   # "score" guard: one collapsed face weighs as SCORE_C pairs
GUARD = _os.environ.get("S1_GUARD", "set")   # "set": no new pair/collapsed face; "count": no more than without the keys (R7)
PREFIX = _os.environ.get("S1_PREFIX", drives.S1_PREFIX)          # R7 fold keys: HGPT_S2_FOLD_
ANGLES_PROP = {f[0]: f[1] for f in drives.S1_FAMILIES}[PREFIX]
SIDES = ("l", "r")
ZONE_Z, ZONE_X = 1.22, 0.12
GIRDLE = ("clavicle_", "scapula_")


elevation_deg = drives.elevation_deg


ZONE_MODE = _os.environ.get("S1_ZONE", "helper")   # "helper": the W3A helper zone (R2); "stretch": measured (R6)
STRETCH_RATIO = float(_os.environ.get("S1_SRATIO", 1.3))
STRETCH_RINGS = int(_os.environ.get("S1_SRINGS", 6))


def stretch_zones(result, adj, V0, F, ht=160):
    """Per side: vertices of faces stretched > STRETCH_RATIO (area vs rest) at the coupled `ht` pose with all drives on,
    plus STRETCH_RINGS rings - the skin that has to share the stretch (R6: lateral back below the armpit and the inner
    upper arm, not the W3A helper zone)."""
    import build_functional_shoulder_correction_blender as correction
    body, rig = result["body"], result["runtime"]
    correction.apply_corrected_pose(result, ht)
    drives.drive(rig, body)
    V, _ = bench._evaluated(body)
    out = {}
    for s in SIDES:
        sign = 1.0 if s == "r" else -1.0                 # F-SIDE-001: runtime _r is +X
        z = {v for f in F if bench._area(V0, f) > 1e-12 and bench._area(V, f) / bench._area(V0, f) > STRETCH_RATIO
             for v in f if V0[v].x * sign > 0.03}
        for _ in range(STRETCH_RINGS):
            z |= {j for i in z for j in adj[i] if V0[j].x * sign > 0.03}
        out[s] = sorted(z)
    bench._reset(rig)
    return out


def fold_zones(result, adj, V0, F, hts=(130, 145, 160)):
    """Per side: vertices of self-intersecting or collapsed (< 0.1 x rest area) faces at the coupled `hts` poses with all
    drives on, plus STRETCH_RINGS rings - the bunched skin on top of the shoulder (R7)."""
    import build_functional_shoulder_correction_blender as correction
    from mathutils.bvhtree import BVHTree
    body, rig = result["body"], result["runtime"]
    seeds = set()
    for ht in hts:
        correction.apply_corrected_pose(result, ht)
        drives.drive(rig, body)
        V, _ = bench._evaluated(body)
        tree = BVHTree.FromPolygons(V, F, all_triangles=True)
        fs = [set(f) for f in F]
        bad = {f for a, b in tree.overlap(tree) if a < b and not (fs[a] & fs[b]) for f in (a, b)}
        bad |= {k for k, f in enumerate(F) if bench._area(V0, f) > 1e-12 and bench._area(V, f) / bench._area(V0, f) < 0.1}
        seeds |= {v for k in bad for v in F[k]}
    out = {}
    for s in SIDES:
        sign = 1.0 if s == "r" else -1.0
        z = {v for v in seeds if V0[v].x * sign > 0.03}
        for _ in range(STRETCH_RINGS):
            z |= {j for i in z for j in adj[i] if V0[j].x * sign > 0.03}
        out[s] = sorted(z)
    bench._reset(rig)
    return out


def zone(body, s):
    names = {g.index: g.name for g in body.vertex_groups}
    sign = 1.0 if s == "r" else -1.0                       # F-SIDE-001: runtime _r is +X
    out = []
    for v in body.data.vertices:
        w = {names[g.group]: g.weight for g in v.groups if g.weight > 0}
        region = sum(x for n, x in w.items() if n.endswith(f"_{s}") and n.startswith(("upperarm_", "deltoid_helper_") + GIRDLE))
        if region > 0.05 and v.co.z > ZONE_Z and v.co.x * sign > ZONE_X:
            out.append(v.index)
    return out


def _normals(V, F):
    N = np.zeros_like(V)
    for f in F:
        a, b, c = V[f[0]], V[f[1]], V[f[2]]
        n = np.cross(b - a, c - a)
        for k in f:
            N[k] += n
    L = np.linalg.norm(N, axis=1, keepdims=True)
    return N / np.maximum(L, 1e-12)


SEP_GAP = float(_os.environ.get("S1_SEPGAP", 0.002))


def separate(Vp, adj, free):
    """Collision resolution in posed space (R7 fold keys): faces touching the free zone that intersect each other are
    pushed apart - each face's vertices behind the other face's plane move out along that face's normal by the
    penetration + SEP_GAP, half each - then the push is lightly smoothed; repeated until the zone has no intersecting pair
    (tangential relaxation cannot untangle two sheets that already pass through each other)."""
    from mathutils.bvhtree import BVHTree
    F = _F[0]
    P = Vp.copy()
    freeset = set(free)
    zf = [k for k, f in enumerate(F) if any(v in freeset for v in f)]
    for _ in range(RELAX_ITERS):
        tree = BVHTree.FromPolygons([Vector(p) for p in P], F, all_triangles=True)
        fs = [set(f) for f in F]
        pairs = [(a, b) for a, b in tree.overlap(tree) if a < b and not (fs[a] & fs[b])
                 and (any(v in freeset for v in F[a]) or any(v in freeset for v in F[b]))]
        if not pairs:
            break
        push = {}
        for a, b in pairs:
            for fa, fb in ((a, b), (b, a)):
                pa, pb = [P[v] for v in F[fa]], [P[v] for v in F[fb]]
                nb = np.cross(pb[1] - pb[0], pb[2] - pb[0])
                L = np.linalg.norm(nb)
                if L < 1e-12:
                    continue
                nb /= L
                cb = sum(pb) / 3.0
                side = np.sign(np.dot(sum(pa) / 3.0 - cb, nb)) or 1.0      # keep fa on the side its centroid is on
                for v in F[fa]:
                    if v not in freeset:
                        continue
                    d = side * np.dot(P[v] - cb, nb)
                    if d < SEP_GAP:
                        push[v] = push.get(v, np.zeros(3)) + side * nb * (SEP_GAP - d) * 0.5
        for v, d in push.items():
            P[v] = P[v] + d
        disp = {i: P[i] - Vp[i] for i in free}                     # one smoothing pass of the displacement
        for i in free:
            nb_ = [disp[j] for j in adj[i] if j in disp]
            if nb_:
                P[i] = Vp[i] + 0.5 * disp[i] + 0.5 * sum(nb_) / len(nb_)
    return P


def relax(Vp, V0, adj, free):
    """Tangential spring relaxation of the free vertices toward rest edge lengths (others fixed)."""
    if RELAX_MODE == "separate":
        return separate(Vp, adj, free)
    if RELAX_MODE in ("smooth", "taubin"):     # Laplacian: flattens crumpled / folded skin (R7); "taubin" alternates a
        P = Vp.copy()                          # negative step so the zone does not shrink (plain smoothing slid it ~59 mm)
        free = list(free)
        for it in range(RELAX_ITERS):
            step = RELAX_STEP if RELAX_MODE == "smooth" or it % 2 == 0 else -1.06 * RELAX_STEP
            new = {i: P[i] + step * (sum(P[j] for j in adj[i]) / len(adj[i]) - P[i]) for i in free}
            for i, p in new.items():
                P[i] = p
        return P
    P = Vp.copy()
    N = _normals(Vp, _F[0])
    free = list(free)
    for _ in range(RELAX_ITERS):
        new = {}
        for i in free:
            acc = np.zeros(3)
            for j in adj[i]:
                d = P[i] - P[j]
                ln = np.linalg.norm(d)
                L0 = np.linalg.norm(V0[i] - V0[j])
                if RELAX_MODE == "pull":
                    L0 = min(L0, ln)
                elif RELAX_MODE == "push":                     # only lengthen compressed edges (unbunch folds)
                    L0 = max(L0, ln)
                acc += P[j] + (d / ln * L0 if ln > 1e-12 else 0.0)
            t = acc / len(adj[i]) - P[i]
            t -= N[i] * t.dot(N[i])
            new[i] = P[i] + RELAX_STEP * t
        for i, p in new.items():
            P[i] = p
    return P


_F = [None]


def build(result):
    body, rig = result["body"], result["runtime"]
    import build_functional_shoulder_correction_blender as correction
    names = {g.index: g.name for g in body.vertex_groups}
    deform = [b.name for b in rig.data.bones if b.use_deform]
    W = [{names[g.group]: g.weight for g in v.groups if names[g.group] in deform and g.weight > 0} for v in body.data.vertices]
    adj = [set() for _ in body.data.vertices]
    for e in body.data.edges:
        a, b = e.vertices
        adj[a].add(b); adj[b].add(a)
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    bench._reset(rig)
    V0l, F = bench._evaluated(body)
    _F[0] = F
    V0 = np.array([tuple(v) for v in V0l])
    zones = (stretch_zones(result, adj, V0l, F) if ZONE_MODE == "stretch" else
             fold_zones(result, adj, V0l, F) if ZONE_MODE == "fold" else {s: zone(body, s) for s in SIDES})
    log, key_angles = {"zone_mode": ZONE_MODE, "zone_vertices": {s: len(z) for s, z in zones.items()}}, {}
    for ht in KEYS_HT:
        correction.apply_corrected_pose(result, ht)
        drives.drive(rig, body)
        Vl, _ = bench._evaluated(body)
        Vp = np.array([tuple(v) for v in Vl])
        mats = {n: np.array((rig.pose.bones[n].matrix @ rig.data.bones[n].matrix_local.inverted()).to_3x3()) for n in deform}
        key_angles[ht] = {s: elevation_deg(rig, s) for s in SIDES}
        entry = {}
        for s in SIDES:
            kb = body.shape_key_add(name=f"{PREFIX}{s}_{ht}", from_mix=False)
            kb.value = 0.0
            if ht in ZERO_KEYS:                       # empty closing key: the previous key fades out by this elevation
                entry[s] = {"closing_key": True, "elevation_deg": round(key_angles[ht][s], 2)}
                continue
            P = relax(Vp, V0, adj, zones[s])
            sig_min, clipped, maxd, maxp = 1.0, 0, 0.0, 0.0
            rest_d = {}
            for i in zones[s]:
                dv = P[i] - Vp[i]
                maxp = max(maxp, float(np.linalg.norm(dv)))
                A = sum(x * mats[nm] for nm, x in W[i].items())
                U, sv, Vt = np.linalg.svd(A)
                sig_min = min(sig_min, float(sv.min()))
                dr = Vt.T @ np.diag(sv / (sv ** 2 + DAMP ** 2)) @ U.T @ dv
                L = float(np.linalg.norm(dr))
                if L > DELTA_CAP_M:
                    dr *= DELTA_CAP_M / L
                    clipped += 1
                maxd = max(maxd, min(L, DELTA_CAP_M))
                rest_d[i] = dr
            for _ in range(DELTA_SMOOTH):                 # rest-space smoothing (removes per-vertex inverse/clip noise);
                rest_d = {i: (rest_d[i] + sum(rest_d.get(j, np.zeros(3)) for j in adj[i])) / (1 + len(adj[i]))
                          for i in zones[s]}               # vertices outside the zone count as 0: no seam
            for i in zones[s]:
                kb.data[i].co = body.data.vertices[i].co + Vector(rest_d[i])
            entry[s] = {"zone_vertices": len(zones[s]), "max_posed_slide_mm": round(maxp * 1000, 2),
                        "max_rest_delta_mm": round(maxd * 1000, 2), "rest_deltas_clipped": clipped,
                        "blended_lbs_sigma_min": round(sig_min, 4), "elevation_deg": round(key_angles[ht][s], 2)}
        if VOLUME_RESTORE and ht not in ZERO_KEYS:
            entry["volume"] = _restore_volume(body, ht, zones, adj, F)
        log[str(ht)] = entry
    bench._reset(rig)
    result["s1_angles"] = {s: tuple(key_angles[ht][s] for ht in KEYS_HT) for s in SIDES}
    for s in SIDES:
        rig[f"{ANGLES_PROP}_{s}"] = list(result["s1_angles"][s])
    if BACKOFF:
        log["backoff"] = _backoff(result, zones, adj, F)
        if VOLUME_RESTORE:                             # the guard changed the keys: restore volume again, re-guard
            log["volume_after_guard"] = {}
            for ht in (h for h in KEYS_HT if h not in ZERO_KEYS):
                correction.apply_corrected_pose(result, ht)
                drives.drive(rig, body)
                for kb in body.data.shape_keys.key_blocks:
                    if kb.name.startswith(PREFIX):
                        kb.value = 0.0
                log["volume_after_guard"][str(ht)] = _restore_volume(body, ht, zones, adj, F)
            log["backoff_2"] = _backoff(result, zones, adj, F)
    bench._reset(rig)
    return log


def _volume(body, F):
    V, _ = bench._evaluated(body)
    return sum(V[f[0]].dot(V[f[1]].cross(V[f[2]])) for f in F) / 6.0


def _restore_volume(body, ht, zones, adj, F, probe=0.001, cap=0.008):
    """Give the key pair of this elevation zero volume change at its own pose: a rest-space offset along the rest vertex
    normals, tapered by a smoothed zone indicator (0 at the zone edge), solved by one secant step (linear in alpha)."""
    keys = [body.data.shape_keys.key_blocks[f"{PREFIX}{s}_{ht}"] for s in SIDES]
    me = body.data
    zset = set(zones["l"]) | set(zones["r"])
    ind = {i: 1.0 for i in zset}
    for _ in range(6):
        ind = {i: (ind[i] + sum(ind.get(j, 0.0) for j in adj[i])) / (1 + len(adj[i])) for i in zset}
    for kb in keys:
        kb.value = 0.0
    v_off = _volume(body, F)
    for kb in keys:
        kb.value = 1.0
    v_on = _volume(body, F)
    own = {k: zones[s] for k, s in enumerate(SIDES)}    # each side's key moves only its own side's zone
    base = {(k, i): keys[k].data[i].co.copy() for k in range(2) for i in own[k]}

    def offset(alpha):
        for k, kb in enumerate(keys):
            for i in own[k]:
                kb.data[i].co = base[(k, i)] + me.vertices[i].normal * (alpha * ind[i])
        bpy.context.view_layer.update()
    offset(probe)
    gain = (_volume(body, F) - v_on) / probe
    alpha = max(-cap, min(cap, (v_off - v_on) / gain)) if abs(gain) > 1e-12 else 0.0
    offset(alpha)
    v_new = _volume(body, F)
    for kb in keys:
        kb.value = 0.0
    bpy.context.view_layer.update()
    return {"key_volume_change_pct": round((v_on - v_off) / v_off * 100, 4), "normal_offset_mm": round(alpha * 1000, 3),
            "after_pct": round((v_new - v_off) / v_off * 100, 4)}


def _bad(body, F, A0):
    """Intersecting face pairs (as frozensets) and collapsed faces (area < 0.1 x rest) of the evaluated mesh."""
    from mathutils.bvhtree import BVHTree
    V, _ = bench._evaluated(body)
    tree = BVHTree.FromPolygons(V, F, all_triangles=True)
    fs = [set(f) for f in F]
    pairs = {(a, b) for a, b in tree.overlap(tree) if a < b and not (fs[a] & fs[b])}
    collapsed = {k for k, f in enumerate(F) if A0[k] > 1e-12 and bench._area(V, f) / A0[k] < 0.1}
    return pairs, collapsed


def _backoff(result, zones, adj, F, rounds=8, rings=int(_os.environ.get("S1_GRINGS", 2)), check=range(95, 161, 5)):
    """Collision/fold guard over the whole driven range: at every CHECK elevation (coupled pose, all drives on), zone
    vertices in intersecting or collapsed faces that the S1-free mesh lacks (+ rings) have their delta halved in every S1 key
    active there, until no check pose adds a pair or a collapsed face."""
    import build_functional_shoulder_correction_blender as correction
    body, rig = result["body"], result["runtime"]
    keys = [kb for kb in body.data.shape_keys.key_blocks if kb.name.startswith(PREFIX)]
    zset = set(zones["l"]) | set(zones["r"])
    side_zone = {s: set(zones[s]) for s in SIDES}
    key = lambda v, sx: (round(sx * v.co.x, 5), round(v.co.y, 5), round(v.co.z, 5))
    by_pos = {key(v, 1.0): v.index for v in body.data.vertices}
    mirror = {v.index: by_pos[key(v, -1.0)] for v in body.data.vertices if key(v, -1.0) in by_pos}
    rest = body.data.vertices
    bench._reset(rig)
    for kb in keys:
        kb.value = 0.0
    V0, _ = bench._evaluated(body)
    A0 = [bench._area(V0, f) for f in F]
    hist = []
    for _pass in range(4):                            # later edits touch keys active at earlier poses: repeat until clean
        passlog = {}
        for ht in check:
            correction.apply_corrected_pose(result, ht)
            drives.drive(rig, body)
            vals = {kb.name: kb.value for kb in keys}
            active = [kb for kb in keys if kb.value > 0]
            if not active:
                continue
            for kb in keys:
                kb.value = 0.0
            base_p, base_c = _bad(body, F, A0)
            h = []
            for _ in range(rounds):
                for kb in keys:
                    kb.value = vals[kb.name]
                p, c = _bad(body, F, A0)
                new_p, new_c = p - base_p, c - base_c
                h.append((len(new_p), len(new_c)))
                if not new_p and not new_c:
                    break
                if GUARD == "count" and len(p) <= len(base_p) and len(c) <= len(base_c):
                    break
                if GUARD == "score" and len(p) + SCORE_C * len(c) <= len(base_p) + SCORE_C * len(base_c):
                    break
                if GUARD in ("count", "score"):       # back off only around the measure that got worse
                    new_p = new_p if len(p) > len(base_p) else set()
                    new_c = new_c if len(c) > len(base_c) else set()
                hit = ({v for a, b in new_p for f in (a, b) for v in F[f] if v in zset}
                       | {v for f in new_c for v in F[f] if v in zset})
                ring = set(hit)
                for _r in range(rings):
                    ring |= {j for i in ring for j in adj[i] if j in zset}
                ring |= {mirror[i] for i in ring if i in mirror and mirror[i] in zset}   # symmetric: both sides back off
                for kb in active:
                    own = side_zone[kb.name.rsplit("_", 2)[1]]
                    for i in ring & own:
                        kb.data[i].co = rest[i].co + (kb.data[i].co - rest[i].co) * 0.5
            passlog[str(ht)] = h
        hist.append(passlog)
        if all(len(h) == 1 for h in passlog.values()):
            break
    for kb in keys:
        kb.value = 0.0
    bpy.context.view_layer.update()
    return {"new_pairs_and_collapsed_per_round": hist}


def sweep(result, use_keys, angles=range(0, 161, 10)):
    import build_functional_shoulder_correction_blender as correction
    body, rig = result["body"], result["runtime"]
    bench._reset(rig)
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    V0, F = bench._evaluated(body)
    dom = bench.dominant_groups(body)
    floor = min(v.z for v in V0)
    rows = []
    for ht in angles:
        correction.apply_corrected_pose(result, ht)
        drives.drive(rig, body)                           # helpers, K1 and (when built) S1
        if not use_keys:
            for kb in body.data.shape_keys.key_blocks:
                if kb.name.startswith(PREFIX):
                    kb.value = 0.0
        V, _ = bench._evaluated(body)
        m = bench.frame_metrics(V0, V, F, dom, floor)
        rows.append({"ht": ht, "collapse": m["collapse_lt_0_1"], "stretch": m["stretch_gt_2"], "pairs": m["self_intersecting_pairs"],
                     "volume_pct": m["body_volume_change_pct"], "area_ratio_max": m["area_ratio_max"]})
    bench._reset(rig)
    return rows


def save(result, out, parent, name="R2"):
    """R2 = R1 + S1 keys (or R6 = R5 + stretch-zone S1 keys): a separate review blend; any in-memory helper bones are
    removed again (67-bone file); the parent's scene markers (e.g. hgpt_shoulder_drive) are kept."""
    import hashlib
    if Path(out).exists():
        raise FileExistsError(out)
    body, rig = result["body"], result["runtime"]
    import build_functional_original_attachment_blender as attachment
    attachment._remove_previous()
    view = bpy.context.view_layer
    for ob in view.objects:
        ob.select_set(False)
    view.objects.active = rig; rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    for s in SIDES:
        for helper in (f"deltoid_helper_{s}", f"shoulder_cap_{s}", f"axilla_{s}", f"hip_crease_{s}"):   # in-memory helpers
            if helper in rig.data.edit_bones:
                rig.data.edit_bones.remove(rig.data.edit_bones[helper])
    bpy.ops.object.mode_set(mode="OBJECT")
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    view.update()
    if sum(b.use_deform for b in rig.data.bones) != 67:
        raise RuntimeError("the review blend must stay a 67-bone file")
    scene = bpy.context.scene
    scene["hgpt_review_candidate"] = f"ORIGINAL_V1_CONSOLIDATED_REVIEW_{name}_CLAUDE"
    scene["hgpt_review_candidate_approved"] = False
    bpy.ops.wm.save_as_mainfile(filepath=str(Path(out).resolve()), copy=True)
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    return {"path": Path(out).name, "sha256": sha(out), "parent": {"path": Path(parent).name, "sha256": sha(parent)},
            "s1_keys": sorted(kb.name for kb in body.data.shape_keys.key_blocks if kb.name.startswith(PREFIX))}


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    get = lambda k: args[args.index(k) + 1] if k in args else None
    bpy.ops.wm.open_mainfile(filepath=str(Path(get("--blend")).resolve()))
    import build_functional_shoulder_correction_blender as correction
    result = correction.build_corrected_scene()
    for kb in result["body"].data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    drives.setup(result)                                 # R5+: anatomical shoulder drive
    drives.install_helpers(result["runtime"])            # R1/R2 lineage only (no-op without W3A data)
    before = sweep(result, False)
    log = build(result)
    after = sweep(result, True)
    for a, b in zip(before, after):
        print("S1", a["ht"], (a["collapse"], a["stretch"], a["pairs"], round(a["volume_pct"], 2)), "->",
              (b["collapse"], b["stretch"], b["pairs"], round(b["volume_pct"], 2)))
    rep = {"kind": "ORIGINAL_V1_S1_SHOULDER_RELAX_DIAGNOSTIC", "approved": False,
           "params": {"keys_ht": KEYS_HT, "activation_start": ACTIVATION_START, "relax_iters": RELAX_ITERS, "relax_mode": RELAX_MODE, "backoff": BACKOFF, "volume_restore": VOLUME_RESTORE, "delta_smooth": DELTA_SMOOTH,
                      "relax_step": RELAX_STEP, "damp": DAMP, "delta_cap_m": DELTA_CAP_M,
                      "zone_mode": ZONE_MODE, "stretch_ratio": STRETCH_RATIO, "stretch_rings": STRETCH_RINGS,
                      "prefix": PREFIX, "zero_keys": ZERO_KEYS, "guard": GUARD, "guard_score_collapse_weight": SCORE_C,
                      "guard_rings": int(_os.environ.get("S1_GRINGS", 2))},
           "solve": log, "key_elevations": result["s1_angles"], "sweep_r1": before, "sweep_r1_s1": after}
    if get("--out"):
        rep["output"] = save(result, get("--out"), get("--blend"), get("--name") or "R2")
    if get("--report"):
        Path(get("--report")).write_text(json.dumps(rep, indent=1) + "\n")
    print("S1LOG", json.dumps(log))


if __name__ == "__main__":
    main()
