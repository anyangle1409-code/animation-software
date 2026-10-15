#!/usr/bin/env python3
"""S5: baked target-shape corrective keys for the full-range overhead press (review only; bpy).  R12 (Claude, 14 Oct 2026).

Owner: "Continue to fix the issue. We can't progress until it's fixed."

R11 (re-meshed shoulder) removed the faceting but kept R10's shapes.  Two measured findings drive S5:
  * a delta-mush deformer (Blender Corrective Smooth, 60 iterations, factor 1.0, shoulder region) on R11 with the S4 sculpt
    shapes re-solved at 5x gives the best-looking press (rounder deltoid, clean armpit fold and hollow, no crease lines) -
    but at runtime it pushes armpit skin through itself (start 50, near top 146-166, lockout 125-193 self-intersecting
    pairs, against 0 / 0 / 1 for R11), and every weaker setting that stays collision-free loses most of the look;
  * so the look is BAKED instead: at each key pose of the full press path the target surface is that delta-mushed shape
    (dumped by dump_targets in its own process), the per-vertex posed offset from R11's surface is mapped to rest through
    R11's blended LBS matrices (damped, capped) into keys HGPT_S5_BAKE_<s>_<ht>, and a count-based, mirror-symmetric guard
    along the press path halves the offsets of vertices in faces the keys would push through each other (or collapse),
    until no pose has more self-intersections or collapsed faces than R11 without the keys.
No new deformer at runtime: R12 = R11 + pose-space keys only (driven by drives.drive_s1 on elevation, family start 60 deg).

  python3.13 build_original_bake_corrective_blender.py -- --dump TARGET.blend --out targets.npz      (own process)
  (the R12 builder then calls build(result, targets))
"""
from __future__ import annotations

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
import build_original_sculpt_corrective_blender as s4  # noqa: E402
import original_v1_press_extension as px  # noqa: E402
import original_v1_review_candidate_drives as drives  # noqa: E402

PREFIX = "HGPT_S5_BAKE_"
KEYS_HT = tuple(float(v) for v in os.environ.get("S5_KEYS", "85,110,130,145,160,172").split(","))
DAMP = 0.05
CAP_M = 0.05
MASK_RINGS = int(os.environ.get("S5_MASK_RINGS", 4))
MASK_PASSES = int(os.environ.get("S5_MASK_PASSES", 30))
POST_SMOOTH = int(os.environ.get("S5_POST_SMOOTH", 0))     # 8 passes weakened the shapes and brought crease lines back
RESOLVE = os.environ.get("S5_RESOLVE", "0") == "1"    # static collision repair of the target: did not converge (rejected)
SMOOTH_GUARD = os.environ.get("S5_SMOOTH_GUARD", "1") == "1"
SIDES = ("l", "r")
_EXTRA = {"paths": []}


def dump_targets(target_blend, out):
    """Posed (all drives + modifiers, incl. the delta mush) vertex positions of the target blend at the key poses."""
    import build_functional_shoulder_correction_blender as correction
    bpy.ops.wm.open_mainfile(filepath=str(Path(target_blend).resolve()))
    res = correction.build_corrected_scene()
    body, rig = res["body"], res["runtime"]
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    drives.setup(res)
    px.install()
    out_d = {}
    for ht in KEYS_HT:
        s4.press_pose(res, ht)
        drives.drive(rig, body)
        V, _ = bench._evaluated(body)
        out_d[str(ht)] = np.array([tuple(v) for v in V])
    np.savez(out, **out_d)


def resolve_collisions(T, F, adj, iters=40, margin=0.0015, step_cap=0.002, smooth_passes=2):
    """Static self-collision repair of a posed target surface: for every pair of non-adjacent intersecting triangles, the
    vertices of each that lie behind the other's plane are pushed out along that plane's normal (half the penetration +
    margin each, capped per iteration); the displacement field is smoothed over the touched vertices + rings; repeated
    until no pair remains or ITERS.  Returns the repaired positions and the remaining pair count."""
    T = T.copy()
    fs = [set(f) for f in F]
    for _ in range(iters):
        tree = BVHTree.FromPolygons([Vector(x) for x in T], F, all_triangles=True)
        pairs = [(a, b) for a, b in tree.overlap(tree) if a < b and not (fs[a] & fs[b])]
        if not pairs:
            return T, 0
        D = {}
        cnt = {}
        for a, b in pairs:
            for fa, fb in ((a, b), (b, a)):
                pa, pb, pc = (T[i] for i in F[fb])
                n = np.cross(pb - pa, pc - pa)
                ln = np.linalg.norm(n)
                if ln < 1e-12:
                    continue
                n /= ln
                for v in F[fa]:
                    d = float(np.dot(T[v] - pa, n))
                    other = np.mean([T[i] for i in F[fa]], axis=0) - pa
                    side = np.sign(np.dot(other, n)) or 1.0      # the side of fb where fa's bulk lies
                    if d * side < margin:
                        push = (margin - d * side) * 0.5
                        D[v] = D.get(v, 0) + n * side * min(push, step_cap)
                        cnt[v] = cnt.get(v, 0) + 1
        if not D:
            return T, len(pairs)
        disp = {v: D[v] / cnt[v] for v in D}
        zone = set(disp)
        for _r in range(smooth_passes):
            zone |= {j for i in zone for j in adj[i]}
        field = {i: disp.get(i, np.zeros(3)) for i in zone}
        for _r in range(smooth_passes):
            field = {i: (field[i] + sum(field.get(j, np.zeros(3)) for j in adj[i])) / (1 + len(adj[i])) for i in zone}
        for i, x in field.items():
            T[i] = T[i] + x
    tree = BVHTree.FromPolygons([Vector(x) for x in T], F, all_triangles=True)
    return T, sum(1 for a, b in tree.overlap(tree) if a < b and not (fs[a] & fs[b]))


def build(result, targets, prefix=None, keys_ht=None, angles_prop="hgpt_s5_angles", extra_guard_paths=None):
    """prefix / keys_ht / angles_prop default to the S5 family; extra_guard_paths: [(name, fn(t))] posed (+ drives) by the
    smooth guard in addition to the full press (R14: the shoulder-press benchmark's own coupled path)."""
    global PREFIX, KEYS_HT
    _EXTRA["paths"] = list(extra_guard_paths or [])
    saved_family = PREFIX, KEYS_HT
    PREFIX = prefix or PREFIX
    KEYS_HT = keys_ht or KEYS_HT
    try:
        return _build(result, targets, angles_prop)
    finally:
        PREFIX, KEYS_HT = saved_family


def _build(result, targets, angles_prop):
    body, rig = result["body"], result["runtime"]
    names = {g.index: g.name for g in body.vertex_groups}
    deform = [b.name for b in rig.data.bones if b.use_deform]
    W = [{names[g.group]: g.weight for g in v.groups if names[g.group] in deform and g.weight > 0} for v in body.data.vertices]
    adj = [set() for _ in body.data.vertices]
    for e in body.data.edges:
        a, b = e.vertices
        adj[a].add(b); adj[b].add(a)
    rest = body.data.vertices
    log, angles = {}, {s: [] for s in SIDES}
    for ht in KEYS_HT:
        bench._reset(rig)
        for kb in body.data.shape_keys.key_blocks[1:]:
            kb.value = 0.0
        s4.press_pose(result, ht)
        drives.drive(rig, body)
        for kb in body.data.shape_keys.key_blocks:
            if kb.name.startswith(PREFIX):
                kb.value = 0.0
        bpy.context.view_layer.update()
        Vl, F = bench._evaluated(body)
        P = np.array([tuple(v) for v in Vl])
        T = targets[str(ht)]
        if T.shape != P.shape:
            raise RuntimeError("target and candidate topology differ")
        if RESOLVE:
            T, left = resolve_collisions(T, F, adj)
            log.setdefault("target_collisions_left", {})[str(ht)] = left
        mats = {n: np.array((rig.pose.bones[n].matrix @ rig.data.bones[n].matrix_local.inverted()).to_3x3()) for n in deform}
        # where the TARGET itself has skin passing through skin, the offset is faded out smoothly (a diffused mask, 0 on
        # those vertices, ~1 MASK_RINGS rings away), so the bake does not carry the target's interpenetration and the
        # guard has little left to cut (stepwise cuts left jagged lines)
        tree = BVHTree.FromPolygons([Vector(x) for x in T], F, all_triangles=True)
        fs = [set(f) for f in F]
        bad = {v for a, b in tree.overlap(tree) if a < b and not (fs[a] & fs[b]) for f in (a, b) for v in F[f]}
        mask = np.ones(len(P))
        if bad:
            near = set(bad)
            for _ in range(MASK_RINGS):
                near |= {j for i in near for j in adj[i]}
            mask[list(near)] = 0.0
            free = [i for i in near if i not in bad]
            for _ in range(MASK_PASSES):
                upd = {i: sum(mask[j] for j in adj[i]) / len(adj[i]) for i in free}
                for i, x in upd.items():
                    mask[i] = x
        off_all = (T - P) * mask[:, None]
        entry = {"target_interpenetrating_vertices": len(bad)}
        for s in SIDES:
            angles[s].append(drives.elevation_deg(rig, s))
            sign = 1.0 if s == "r" else -1.0
            kb = body.shape_key_add(name=f"{PREFIX}{s}_{int(round(ht))}", from_mix=False)
            kb.value = 0.0
            off = off_all
            idx = [i for i in np.where(np.linalg.norm(off, axis=1) > 1e-5)[0] if rest[i].co.x * sign > 0.0]
            clipped, maxp = 0, 0.0
            for i in idx:
                dv = off[i]
                maxp = max(maxp, float(np.linalg.norm(dv)))
                A = sum(x * mats[nm] for nm, x in W[i].items())
                U, sv, Vt = np.linalg.svd(A)
                dr = Vt.T @ np.diag(sv / (sv ** 2 + DAMP ** 2)) @ U.T @ dv
                L = float(np.linalg.norm(dr))
                if L > CAP_M:
                    dr *= CAP_M / L; clipped += 1
                kb.data[i].co = rest[i].co + Vector(dr)
            entry[s] = {"moved": len(idx), "max_posed_mm": round(maxp * 1000, 1), "clipped": clipped,
                        "elevation_deg": round(angles[s][-1], 2)}
        log[str(ht)] = entry
    for s in SIDES:
        rig[f"{angles_prop}_{s}"] = list(angles[s])
    saved = s4.PREFIX
    s4.PREFIX = PREFIX                                   # reuse the S4 press-path guard for this family
    try:
        log["guard"] = smooth_guard(result, adj) if SMOOTH_GUARD else s4._guard(result, adj, rounds=10)
        # the guard's stepwise cut-backs leave seams: smooth every key's rest-space offsets (POST_SMOOTH Laplacian passes,
        # the region border held at zero), then guard again
        keys = [kb for kb in body.data.shape_keys.key_blocks if kb.name.startswith(PREFIX)] if POST_SMOOTH else []
        R0 = np.array([tuple(v.co) for v in rest])
        for kb in keys:
            D = np.array([tuple(d.co) for d in kb.data]) - R0
            act = set(np.where(np.linalg.norm(D, axis=1) > 1e-7)[0])
            zone = act | {j for i in act for j in adj[i]}
            inner = [i for i in zone if adj[i] <= zone]
            for _ in range(POST_SMOOTH):
                upd = {i: (D[i] + sum(D[j] for j in adj[i])) / (1 + len(adj[i])) for i in inner}
                for i, x in upd.items():
                    D[i] = x
            kb.data.foreach_set("co", (R0 + D).reshape(-1))
        log["guard_after_smoothing"] = s4._guard(result, adj, rounds=10)
    finally:
        s4.PREFIX = saved
    bench._reset(rig)
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    return log


def smooth_guard(result, adj, rounds=12, ring=5, passes=25, ts=tuple(i / 20 for i in range(21))):
    """Press-path guard with a SMOOTH back-off: where the S5 keys add self-intersecting pairs or collapsed faces (against
    the same pose without S5), the keys' rest deltas are scaled by 0.5 + 0.5 m, m a diffused mask (0 on the offending
    vertices, rising to 1 over RING rings), mirror-symmetric; repeated until no pose adds any.  The S4 guard's stepwise
    halving of whole rings left jagged seams in the baked shapes."""
    body, rig = result["body"], result["runtime"]
    keys = [kb for kb in body.data.shape_keys.key_blocks if kb.name.startswith(PREFIX)]
    rest = body.data.vertices
    R0 = np.array([tuple(v.co) for v in rest])
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
    poses = [("press", lambda t: px.pose_press_full(result, t))] + _EXTRA["paths"]
    for _pass in range(4):
        passlog = {}
        for (pname, pfn), t in ((pp, t) for pp in poses for t in ts):
            bench._reset(rig)
            pfn(t)
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
                hit |= {mirror[i] for i in hit if i in mirror}
                near = set(hit)
                for _r in range(ring):
                    near |= {j for i in near for j in adj[i]}
                m = {i: (0.0 if i in hit else 1.0) for i in near}
                free = [i for i in near if i not in hit]
                for _r in range(passes):
                    m.update({i: sum(m.get(j, 1.0) for j in adj[i]) / len(adj[i]) for i in free})
                for kb in active:
                    co = np.array([tuple(d.co) for d in kb.data])
                    for i, mi in m.items():
                        co[i] = R0[i] + (co[i] - R0[i]) * (0.5 + 0.5 * mi)
                    kb.data.foreach_set("co", co.reshape(-1))
            passlog[f"{pname}@{t:.2f}"] = h
            for kb in keys:
                kb.value = 0.0
        hist.append(passlog)
        if all(len(x) == 1 for x in passlog.values()):
            break
    bench._reset(rig)
    return {"extra_pairs_and_collapsed_per_round": hist}


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    get = lambda k: args[args.index(k) + 1]
    dump_targets(get("--dump"), get("--out"))


if __name__ == "__main__":
    main()
