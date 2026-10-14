#!/usr/bin/env python3
"""C1: upper-arm / trunk contact corrective (review-only; bpy).  Owner (14 Oct 2026): "fix the blade tilt and row contact".

R4's anatomical arm pivot lets the back of the upper arm pass into the side of the chest when the shoulder extends (bent-over
row: spine_03/upper-arm self-intersections, 46 per side).  C1 is a K1-style pose-space contact corrective:

  per key (shoulder-extension angle reached at fractions KEY_T of the row pull) and side, in that row pose:
    1. contact: every upper-arm-dominant skin vertex within REACH of the trunk skin (spine/pelvis/neck/scapula/clavicle-
       dominant faces) whose signed distance along the trunk face normal is below GAP_M is pushed out to GAP_M (the arm
       skin compresses against the chest instead of passing into it);
    2. the push is extended harmonically over TAPER_RINGS rings of upper-arm skin (zero at the outer ring: no seam);
    3. the posed displacement is mapped to rest space through each vertex's blended LBS matrix and capped;
    4. count-based guard (as K1): over the driven range (row t 0.5..1) the keyed mesh may not have more collapsed faces than
       the key-free mesh; deltas of the newly collapsed faces (+ 2 rings) are halved until it has none extra.
  Keys HGPT_C1_ARMTRUNK_<s>_<n> are driven per side by the measured shoulder extension (angle of the upper arm behind the
  thorax's frontal plane, in the thorax sagittal plane), hats from START_DEG; the key angles are stored on the rig as
  hgpt_c1_angles_<s>.  scripts/original_v1_review_candidate_drives.drive_c1 drives them.
"""
from __future__ import annotations

import math
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

PREFIX = "HGPT_C1_ARMTRUNK_"
KEY_T = (0.875, 1.0)           # row frames with arm/trunk contact (shoulder extension ~25 and ~38 deg)
_E = __import__('os').environ
GAP_M = float(_E.get('C1_GAP', 0.004))   # 2 mm left 47 pairs at full pull, 6-8 mm folded the arm skin; 4 mm: 32
REACH_M = float(_E.get('C1_REACH', 0.04))
TAPER_RINGS = 4
DELTA_CAP_M = 0.03
START_DEG = 18.0             # above the walk stride arm swing (~15 deg extension): C1 stays off there
SIDES = ("l", "r")
TRUNK = ("spine", "pelvis", "neck", "scapula", "clavicle", "root")


def extension_deg(rig, s):
    """Shoulder extension: angle of the upper arm behind the thorax frontal plane, measured in the thorax sagittal plane
    (0 = hanging, + = behind the trunk, - = in front)."""
    pb = rig.pose.bones
    sp = pb["spine_03"]
    rot = sp.matrix.to_3x3() @ rig.data.bones["spine_03"].matrix_local.to_3x3().inverted()
    back, down = rot @ Vector((0, 1, 0)), rot @ Vector((0, 0, -1))
    arm = (pb[f"upperarm_{s}"].tail - pb[f"upperarm_{s}"].head).normalized()
    return math.degrees(math.atan2(arm.dot(back), arm.dot(down)))


def _row_pose(result, t):
    rig = result["runtime"]
    heads = result["_c1_heads"]
    import build_functional_original_coupled_motion_blender as coupled
    bench.pose_row(rig, t, heads, coupled.clavicle_basis)
    bpy.context.view_layer.update()


def build(result):
    body, rig = result["body"], result["runtime"]
    names = {g.index: g.name for g in body.vertex_groups}
    deform = [b.name for b in rig.data.bones if b.use_deform]
    W = [{names[g.group]: g.weight for g in v.groups if names[g.group] in deform and g.weight > 0} for v in body.data.vertices]
    adj = [set() for _ in body.data.vertices]
    for e in body.data.edges:
        a, b = e.vertices
        adj[a].add(b); adj[b].add(a)
    bench._reset(rig)
    result["_c1_heads"] = {s: rig.pose.bones[f"foot_{s}"].head.copy() for s in SIDES}
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    dom = bench.dominant_groups(body)
    log, angles = {}, {s: [] for s in SIDES}
    for n, t in enumerate(KEY_T):
        _row_pose(result, t)
        V, F = bench._evaluated(body)
        mats = {nm: np.array((rig.pose.bones[nm].matrix @ rig.data.bones[nm].matrix_local.inverted()).to_3x3()) for nm in deform}
        trunk_faces = [k for k, f in enumerate(F) if sum(dom[v].split("_")[0] in TRUNK for v in f) >= 2]
        tree = BVHTree.FromPolygons(V, [F[k] for k in trunk_faces], all_triangles=True)
        entry = {}
        for s in SIDES:
            angles[s].append(extension_deg(rig, s))
            arm = [i for i, g in enumerate(dom) if g == f"upperarm_{s}"]
            fixed = {}
            for i in arm:
                loc, nrm, idx, d = tree.find_nearest(V[i], REACH_M)
                if loc is None:
                    continue
                sd = (V[i] - loc).dot(nrm)
                if sd < GAP_M:
                    fixed[i] = nrm * (GAP_M - sd)
            ring = {i: 0 for i in fixed}
            frontier = list(fixed)
            armset = set(arm)
            for r in range(1, TAPER_RINGS + 1):
                nxt = []
                for i in frontier:
                    for j in adj[i]:
                        if j in armset and j not in ring:
                            ring[j] = r; nxt.append(j)
                frontier = nxt
            field = {i: fixed.get(i, Vector()) for i in ring}
            free = [i for i, r in ring.items() if 0 < r < TAPER_RINGS]
            for _ in range(60):
                for i in free:
                    nb = [field[j] for j in adj[i] if j in field]
                    field[i] = sum(nb, Vector()) / len(nb)
            kb = body.shape_key_add(name=f"{PREFIX}{s}_{n}", from_mix=False)
            kb.value = 0.0
            clipped, maxd = 0, 0.0
            for i, dv in field.items():
                if dv.length < 1e-7:
                    continue
                A = sum(x * mats[nm] for nm, x in W[i].items())
                dr = np.linalg.solve(A, np.array(dv))
                L = float(np.linalg.norm(dr))
                if L > DELTA_CAP_M:
                    dr *= DELTA_CAP_M / L; clipped += 1
                maxd = max(maxd, min(L, DELTA_CAP_M))
                kb.data[i].co = body.data.vertices[i].co + Vector(dr)
            entry[s] = {"extension_deg": round(angles[s][-1], 2), "contact_vertices": len(fixed), "taper_vertices": len(free),
                        "max_posed_push_mm": round(max((v.length for v in fixed.values()), default=0) * 1000, 2),
                        "max_rest_delta_mm": round(maxd * 1000, 2), "clipped": clipped}
        log[str(t)] = entry
    for s in SIDES:
        rig[f"hgpt_c1_angles_{s}"] = list(angles[s])
    log["guard"] = _guard(result, adj)
    bench._reset(rig)
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    return log


def _guard(result, adj, rounds=8, rings=2, ts=tuple(0.5 + 0.05 * i for i in range(11))):
    import original_v1_review_candidate_drives as drives
    body, rig = result["body"], result["runtime"]
    keys = [kb for kb in body.data.shape_keys.key_blocks if kb.name.startswith(PREFIX)]
    rest = body.data.vertices
    bench._reset(rig)
    for kb in keys:
        kb.value = 0.0
    V0, F = bench._evaluated(body)
    A0 = [bench._area(V0, f) for f in F]
    moved = {kb.name: {i for i, d in enumerate(kb.data) if (d.co - rest[i].co).length > 1e-9} for kb in keys}

    def bad():
        V, _ = bench._evaluated(body)
        tree = BVHTree.FromPolygons(V, F, all_triangles=True)
        fs = [set(f) for f in F]
        pairs = {(a, b) for a, b in tree.overlap(tree) if a < b and not (fs[a] & fs[b])}
        return pairs, {k for k, f in enumerate(F) if A0[k] > 1e-12 and bench._area(V, f) / A0[k] < 0.1}
    hist = []
    for _pass in range(4):
        passlog = {}
        for t in ts:
            _row_pose(result, t)
            drives.drive_c1(rig, body)
            vals = {kb.name: kb.value for kb in keys}
            active = [kb for kb in keys if kb.value > 0]
            if not active:
                continue
            for kb in keys:
                kb.value = 0.0
            base_p, base_c = bad()
            hh = []
            for _ in range(rounds):
                for kb in keys:
                    kb.value = vals[kb.name]
                p, c = bad()
                hh.append((len(p) - len(base_p), len(c) - len(base_c)))
                if len(c) <= len(base_c):                    # the push only removes pairs; guard the folds
                    break
                new_c = c - base_c
                ring = {v for f in new_c for v in F[f]}
                for _r in range(rings):
                    ring |= {j for i in ring for j in adj[i]}
                for kb in active:
                    for i in ring & moved[kb.name]:
                        kb.data[i].co = rest[i].co + (kb.data[i].co - rest[i].co) * 0.5
            passlog[f"{t:.2f}"] = hh
            for kb in keys:
                kb.value = 0.0
        hist.append(passlog)
        if all(len(x) == 1 for x in passlog.values()):
            break
    bench._reset(rig)
    return {"extra_pairs_and_collapsed_per_round": hist}
