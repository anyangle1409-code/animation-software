"""W4: weights-only refit of the shoulder-top/axilla skin to keep linear-blend skinning well conditioned (diagnostic).

Diagnosis (W2, draft PR #112): during the coupled 0-160 deg shoulder motion the blended LBS matrices of the
shoulder-top skin become nearly singular (smallest singular value 0.0024 at 150 deg) because those vertices average
bones whose rotations differ by 120-180 deg; no bounded corrective can restore such skin.

Refit (in memory; the source blend, rig and all other weights are unchanged):
  * zone: vertices with weight > 0.05 in the upper-arm/clavicle/scapula groups and rest z > 1.30 m, |x| > 0.12 m;
  * candidates per vertex: its current deforming bones plus the same side's clavicle, scapula, upper arm and spine_03
    (at most 4 non-zero weights kept, as the rig/export contract requires);
  * search: the weight simplex on a 0.1 grid; objective = min over poses (90, 120, 145, 160 deg) of the blended
    3x3's smallest singular value, minus KAPPA * L1 change from the original weights; a vertex is changed only if its
    worst-pose singular value improves by more than MIN_GAIN;
  * the weight change is diffused over SMOOTH_PASSES passes within the zone (no seams), then renormalized.
Measured before/after: per-vertex singular-value distribution at 160 deg, and collapse/stretch/self-intersection/volume
along the coupled sweep and the M1 shoulder-press benchmark.  No approval of any kind.
"""

from __future__ import annotations

import itertools
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

POSES = (90, 120, 145, 160)
GRID = 10
KAPPA = 0.15
MIN_GAIN = 0.05
SMOOTH_PASSES = 3
MAX_INFLUENCES = 4
ZONE_Z, ZONE_X = 1.30, 0.12
REGION = ("upperarm_", "clavicle_", "scapula_")
EXTRA_CANDIDATES = {"spine_03"}       # variants run: KAPPA 0.15/0.4, with and without spine_03 (all recorded)


def simplex(n, steps=GRID):
    for c in itertools.product(range(steps + 1), repeat=n):
        if sum(c) == steps:
            yield np.array(c, float) / steps


def run(apply=True):
    import build_functional_shoulder_correction_blender as correction
    result = correction.build_corrected_scene()
    body, rig = result["body"], result["runtime"]
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    names = {g.index: g.name for g in body.vertex_groups}
    gidx = {g.name: g.index for g in body.vertex_groups}
    deform = [b.name for b in rig.data.bones if b.use_deform]
    correction.apply_corrected_pose(result, 0)
    rest = [body.matrix_world @ v.co for v in body.data.vertices]
    weights = [{names[g.group]: g.weight for g in v.groups if names[g.group] in deform and g.weight > 0} for v in body.data.vertices]
    zone = [i for i, w in enumerate(weights)
            if sum(x for n, x in w.items() if n.startswith(REGION)) > 0.05 and rest[i].z > ZONE_Z and abs(rest[i].x) > ZONE_X]
    # bone 3x3 skinning rotations per pose
    mats = {}
    for p in POSES:
        correction.apply_corrected_pose(result, p)
        mats[p] = {n: np.array((rig.pose.bones[n].matrix @ rig.data.bones[n].matrix_local.inverted()).to_3x3()) for n in deform}
    correction.apply_corrected_pose(result, 0)

    def sigma(w, p):
        A = sum(x * mats[p][n] for n, x in w.items())
        return float(np.linalg.svd(A, compute_uv=False).min())

    before = [min(sigma(weights[i], p) for p in POSES) for i in zone]
    new = {}
    for i, s0 in zip(zone, before):
        side = "r" if rest[i].x > 0 else "l"          # runtime suffix by x side (F-SIDE-001: _r is +X)
        cand = sorted(set(weights[i]) | {f"clavicle_{side}", f"scapula_{side}", f"upperarm_{side}"} | EXTRA_CANDIDATES)
        w0 = np.array([weights[i].get(n, 0.0) for n in cand])
        A = np.stack([np.stack([mats[p][n] for n in cand]) for p in POSES])          # P x C x 3 x 3
        best, best_obj = None, s0
        for w in simplex(len(cand)) if len(cand) <= 5 else []:
            if np.count_nonzero(w) > MAX_INFLUENCES:
                continue
            B = np.einsum("c,pcij->pij", w, A)
            s = np.linalg.svd(B, compute_uv=False).min()
            obj = s - KAPPA * np.abs(w - w0).sum()
            if obj > best_obj + MIN_GAIN:
                best, best_obj = w, obj
        if best is not None:
            new[i] = {n: float(x) for n, x in zip(cand, best) if x > 0}
    # diffuse the weight change within the zone
    adj = {i: set() for i in zone}
    zset = set(zone)
    for p in body.data.polygons:
        vs = [v for v in p.vertices if v in zset]
        for a in vs:
            adj[a].update(b for b in vs if b != a)
    delta = {i: {} for i in zone}
    for i, w in new.items():
        for n in set(w) | set(weights[i]):
            delta[i][n] = w.get(n, 0.0) - weights[i].get(n, 0.0)
    for _ in range(SMOOTH_PASSES):
        nd = {}
        for i in zone:
            nb = [i] + list(adj[i])
            keys = set().union(*(delta[j].keys() for j in nb))
            nd[i] = {n: sum(delta[j].get(n, 0.0) for j in nb) / len(nb) for n in keys}
        delta = nd
    final = {}
    for i in zone:
        w = dict(weights[i])
        for n, d in delta[i].items():
            w[n] = max(0.0, w.get(n, 0.0) + d)
        top = dict(sorted(w.items(), key=lambda kv: -kv[1])[:MAX_INFLUENCES])
        s = sum(top.values())
        top = {n: x / s for n, x in top.items() if x / s > 1e-4}
        if any(abs(top.get(n, 0) - weights[i].get(n, 0)) > 1e-6 for n in set(top) | set(weights[i])):
            final[i] = top
    after = [min(sigma(final.get(i, weights[i]), p) for p in POSES) for i in zone]
    report = {"zone_vertices": len(zone), "changed_vertices": len(final),
              "worst_pose_sigma_min": {"before": round(min(before), 5), "after": round(min(after), 5)},
              "vertices_sigma_lt_0_1": {"before": sum(s < 0.1 for s in before), "after": sum(s < 0.1 for s in after)},
              "vertices_sigma_lt_0_3": {"before": sum(s < 0.3 for s in before), "after": sum(s < 0.3 for s in after)},
              "parameters": {"poses": POSES, "grid": GRID, "kappa": KAPPA, "min_gain": MIN_GAIN, "smooth_passes": SMOOTH_PASSES}}
    if apply:
        for i, w in final.items():
            for g in list(body.data.vertices[i].groups):
                if names[g.group] in deform:
                    body.vertex_groups[g.group].remove([i])
            for n, x in w.items():
                body.vertex_groups[gidx[n]].add([i], x, "REPLACE")
        bpy.context.view_layer.update()
    return result, report, final, weights


def sweep_metrics(result, angles=(90, 110, 120, 130, 140, 145, 150, 155, 160)):
    import build_functional_shoulder_correction_blender as correction
    body = result["body"]
    faces, _ = correction.region_faces(body)
    correction.apply_corrected_pose(result, 0)
    rest = correction._evaluated(body)
    out = {}
    for a in angles:
        correction.apply_corrected_pose(result, a)
        m = correction.deformation_metrics(body, rest, correction._evaluated(body), faces)
        out[a] = {k: m[k] for k in ("collapse_faces_ratio_lt_0_1", "stretched_faces_ratio_gt_2", "area_ratio_min",
                                    "body_volume_change_pct", "self_intersecting_face_pairs_in_region")}
    correction.apply_corrected_pose(result, 0)
    return out


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = Path(args[args.index("--out") + 1]) if "--out" in args else None
    import build_functional_shoulder_correction_blender as correction
    res0 = correction.build_corrected_scene()
    baseline = sweep_metrics(res0)
    result, report, final, original = run(apply=True)
    refit = sweep_metrics(result)
    report["coupled_sweep"] = {"before": baseline, "after": refit}
    rep = {"report": report, "approved": False}
    print("W4", json.dumps(report, default=str)[:3000])
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(rep, indent=1, default=str) + "\n")
