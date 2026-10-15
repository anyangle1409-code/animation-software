#!/usr/bin/env python3
"""H1: baked delta-mush hip-crease keys (review only; bpy).  R13 (Claude, 15 Oct 2026).  Owner: "Yes. Continue" (the hip
fold with the shoulder recipe).

R12's deepest remaining folds are the groin crease in the squat (227 self-intersecting pairs, 28 collapsed faces) and the
deadlift (313 / 38).  The shoulder recipe, measured on R12 + the hip-crease helper joint (original_v1_hip_crease_helper):
  * the helper alone: squat 227 -> 120 pairs, collapse 28 -> 4, but the deadlift gets worse (313 -> 411: at 135 deg the
    helper band folds onto itself) and stretch doubles;
  * helper + a delta-mush deformer (Corrective Smooth, 60 iterations, factor 1.0, full within 14 cm of each hip joint,
    cosine fade to 22 cm): squat 124 pairs / 2 collapsed, deadlift 283 / 2, stretch back to R12 - the look wanted - but
    live it adds 9-16 pairs in the lunge and single-leg stance (0 in R12) and is a new runtime deformer;
  * so, as S5 for the shoulder, the look is BAKED: at each key hip flexion (squat path up to 110 deg, deadlift path at
    135) the delta-mushed surface (dumped from the target blend in its own process) minus the candidate's surface is
    mapped to rest through the blended LBS matrices (damped, capped) into keys HGPT_H1_BAKE_<s>_<deg>, driven by
    original_v1_hip_crease_helper.drive_h1 on sagittal hip flexion (start 20 deg); vertices on the midline get half of
    the offset in each side's key.  Then a smooth, mirror-symmetric guard over every hip benchmark path (squat, deadlift,
    lunge, single-leg stance, walk, bent-over row) scales the keys' deltas by 0.5 + 0.5 m (m a diffused mask, 0 on the
    offending vertices) wherever they add self-intersecting pairs or collapsed faces, until no frame adds any.

  python3.13 build_original_hip_bake_corrective_blender.py -- --dump TARGET.blend --out targets.npz      (own process)
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
import original_v1_hip_crease_helper as hip  # noqa: E402
import original_v1_review_candidate_drives as drives  # noqa: E402

PREFIX = hip.H1_PREFIX
KEYS_DEG = tuple(float(v) for v in os.environ.get("H1_KEYS", "45,70,90,110,135").split(","))
SQUAT_MAX_DEG = 110.0
DAMP = 0.05
CAP_M = 0.05
MIDLINE_M = 1e-4             # vertices this close to x = 0 are midline (the mesh's midline is not exactly at 0)
GUARD_PATHS = ("squat", "deadlift", "lunge", "single_leg_stance", "walk_stride", "bent_over_row")
GUARD_TS = tuple(i / 16 for i in range(17))
SIDES = ("l", "r")


def plans(result):
    import build_functional_original_coupled_motion_blender as coupled
    body, rig = result["body"], result["runtime"]
    heads = result.setdefault("_h1_heads", {s: rig.pose.bones[f"foot_{s}"].head.copy() for s in SIDES})
    return {"squat": lambda t: bench.pose_squat(rig, t, heads), "deadlift": lambda t: bench.pose_deadlift(rig, t, heads),
            "lunge": lambda t: bench.pose_lunge(rig, body, t), "single_leg_stance": lambda t: bench.pose_single_leg(rig, body, t),
            "walk_stride": lambda t: bench.pose_walk(rig, body, t),
            "bent_over_row": lambda t: bench.pose_row(rig, t, heads, coupled.clavicle_basis)}


def key_pose(result, deg):
    """The squat (deg <= 110) or deadlift path pose whose hip flexion is deg (bisection on t; both paths are monotone)."""
    rig = result["runtime"]
    fn = plans(result)["squat" if deg <= SQUAT_MAX_DEG else "deadlift"]
    lo, hi = 0.0, 1.0
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        bench._reset(rig)
        fn(mid)
        bpy.context.view_layer.update()
        if hip.hip_flexion_deg(rig, "r") < deg:
            lo = mid
        else:
            hi = mid
    bench._reset(rig)
    fn(0.5 * (lo + hi))
    bpy.context.view_layer.update()


def _rest_state(result):
    body, rig = result["body"], result["runtime"]
    bench._reset(rig)
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    V0, _ = bench._evaluated(body)
    bench.REST_FLOOR[0] = min(v.z for v in V0)
    result.setdefault("_h1_heads", {s: rig.pose.bones[f"foot_{s}"].head.copy() for s in SIDES})


def dump_targets(target_blend, out):
    """Posed vertex positions (all drives + modifiers, incl. the hip delta mush) of the target blend at the key angles."""
    import build_functional_shoulder_correction_blender as correction
    bpy.ops.wm.open_mainfile(filepath=str(Path(target_blend).resolve()))
    res = correction.build_corrected_scene()
    body, rig = res["body"], res["runtime"]
    drives.setup(res)
    _rest_state(res)
    out_d = {}
    for deg in KEYS_DEG:
        key_pose(res, deg)
        drives.drive(rig, body)
        V, _ = bench._evaluated(body)
        out_d[str(deg)] = np.array([tuple(v) for v in V])
    np.savez(out, **out_d)


def build(result, targets):
    body, rig = result["body"], result["runtime"]
    _rest_state(result)
    names = {g.index: g.name for g in body.vertex_groups}
    deform = [b.name for b in rig.data.bones if b.use_deform]
    W = [{names[g.group]: g.weight for g in v.groups if names[g.group] in deform and g.weight > 0} for v in body.data.vertices]
    adj = [set() for _ in body.data.vertices]
    for e in body.data.edges:
        a, b = e.vertices
        adj[a].add(b); adj[b].add(a)
    rest = body.data.vertices
    log, angles = {}, {s: [] for s in SIDES}
    for deg in KEYS_DEG:
        for kb in body.data.shape_keys.key_blocks[1:]:
            kb.value = 0.0
        key_pose(result, deg)
        drives.drive(rig, body)
        for kb in body.data.shape_keys.key_blocks:
            if kb.name.startswith(PREFIX):
                kb.value = 0.0
        bpy.context.view_layer.update()
        Vl, F = bench._evaluated(body)
        P = np.array([tuple(v) for v in Vl])
        T = targets[str(deg)]
        if T.shape != P.shape:
            raise RuntimeError("target and candidate topology differ")
        off = T - P
        mats = {n: np.array((rig.pose.bones[n].matrix @ rig.data.bones[n].matrix_local.inverted()).to_3x3()) for n in deform}
        entry = {}
        for s in SIDES:
            angles[s].append(hip.hip_flexion_deg(rig, s))
            sign = 1.0 if s == "r" else -1.0
            kb = body.shape_key_add(name=f"{PREFIX}{s}_{int(round(deg))}", from_mix=False)
            kb.value = 0.0
            idx = [i for i in np.where(np.linalg.norm(off, axis=1) > 1e-5)[0]
                   if rest[i].co.x * sign >= 0.0 or abs(rest[i].co.x) < MIDLINE_M]
            clipped, maxp = 0, 0.0
            for i in idx:
                dv = off[i] * (0.5 if abs(rest[i].co.x) < MIDLINE_M else 1.0)     # midline: half in each side's key
                maxp = max(maxp, float(np.linalg.norm(dv)))
                A = sum(x * mats[nm] for nm, x in W[i].items())
                U, sv, Vt = np.linalg.svd(A)
                dr = Vt.T @ np.diag(sv / (sv ** 2 + DAMP ** 2)) @ U.T @ dv
                L = float(np.linalg.norm(dr))
                if L > CAP_M:
                    dr *= CAP_M / L; clipped += 1
                kb.data[i].co = rest[i].co + Vector(dr)
            entry[s] = {"moved": len(idx), "max_posed_mm": round(maxp * 1000, 1), "clipped": clipped,
                        "hip_flexion_deg": round(angles[s][-1], 2)}
        log[str(deg)] = entry
    for s in SIDES:
        rig[f"hgpt_h1_angles_{s}"] = list(angles[s])
    log["guard"] = smooth_guard(result, adj)
    bench._reset(rig)
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    return log


def smooth_guard(result, adj, rounds=12, ring=5, passes=25):
    """The S5 smooth guard (build_original_bake_corrective_blender.smooth_guard) over the hip benchmark paths."""
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
    paths = plans(result)

    def bad():
        V, _ = bench._evaluated(body)
        tree = BVHTree.FromPolygons(V, F, all_triangles=True)
        return ({(a, b) for a, b in tree.overlap(tree) if a < b and not (fs[a] & fs[b])},
                {k for k, f in enumerate(F) if A0[k] > 1e-12 and bench._area(V, f) / A0[k] < 0.1})
    hist = []
    for _pass in range(4):
        passlog = {}
        for path in GUARD_PATHS:
            for t in GUARD_TS:
                bench._reset(rig)
                paths[path](t)
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
                passlog[f"{path}@{t:.3f}"] = h
                for kb in keys:
                    kb.value = 0.0
        hist.append(passlog)
        print("H1 guard pass", _pass, sum(len(x) > 1 for x in passlog.values()), "frames cut", flush=True)
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
