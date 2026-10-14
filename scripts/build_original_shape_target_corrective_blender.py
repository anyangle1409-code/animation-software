#!/usr/bin/env python3
"""S3: shape-target corrective keys (review-only; bpy).  R9 (Claude, 14 Oct 2026).

R8's shoulder-cap helper removed the top-of-shoulder fold at 120-160 deg but, at mid elevation (45-100 deg), leaves the skin
above the glenohumeral pivot up to 45 mm proud of R5's surface (the "shoulder pad"; body volume +1.4 % at 90 deg vs R5
+0.2 %).  R5's skin is right there (its problem began above 120 deg).  S3 keys pull the skin above the pivot back to the
REFERENCE blend's posed surface at a few mid elevations and fade out before the fold range:

  per key elevation and side: posed reference surface (same coupled pose, all reference drives) -> per-vertex posed target
  for zone vertices (rest z above pivot - Z_BELOW, within RADIUS of the pivot, moved > MIN_MM vs the reference); the posed
  offset is tapered over TAPER_RINGS rings, mapped to rest through the blended LBS matrices (damped), capped;
  keys HGPT_S3_SHAPE_<s>_<ht> with an empty closing key at CLOSE_HT, driven by drives.drive_s1 (family start START_DEG).
"""
from __future__ import annotations

import json
import os
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

_E = os.environ
PREFIX = "HGPT_S3_SHAPE_"
KEYS_HT = tuple(int(v) for v in _E.get("S3_KEYS", "45,75,100").split(","))
CLOSE_HT = int(_E.get("S3_CLOSE", 125))
START_DEG = float(_E.get("S3_START", 20))
RADIUS = float(_E.get("S3_RADIUS", 0.20))
Z_BELOW = float(_E.get("S3_ZBELOW", 0.03))
MIN_MM = float(_E.get("S3_MIN_MM", 2.0))
TAPER_RINGS = int(_E.get("S3_RINGS", 4))
DAMP = 0.05
CAP_M = 0.04
SIDES = ("l", "r")


def reference_surfaces(ref_blend, hts):
    """Posed vertex positions of the reference blend (all its drives) at each coupled elevation."""
    import build_functional_shoulder_correction_blender as correction
    bpy.ops.wm.open_mainfile(filepath=str(Path(ref_blend).resolve()))
    res = correction.build_corrected_scene()
    body, rig = res["body"], res["runtime"]
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    drives.setup(res)
    out = {}
    for ht in hts:
        correction.apply_corrected_pose(res, ht)
        drives.drive(rig, body)
        V, _ = bench._evaluated(body)
        out[ht] = np.array([tuple(v) for v in V])
    bench._reset(rig)
    return out


def build(result, refs):
    import build_functional_shoulder_correction_blender as correction
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
    for ht in KEYS_HT + (CLOSE_HT,):
        bench._reset(rig)
        for kb in body.data.shape_keys.key_blocks[1:]:
            kb.value = 0.0
        correction.apply_corrected_pose(result, ht)
        drives.drive(rig, body)
        for kb in body.data.shape_keys.key_blocks:
            if kb.name.startswith(PREFIX):
                kb.value = 0.0
        bpy.context.view_layer.update()
        V, _ = bench._evaluated(body)
        P = np.array([tuple(v) for v in V])
        mats = {n: np.array((rig.pose.bones[n].matrix @ rig.data.bones[n].matrix_local.inverted()).to_3x3()) for n in deform}
        entry = {}
        for s in SIDES:
            angles[s].append(drives.elevation_deg(rig, s))
            kb = body.shape_key_add(name=f"{PREFIX}{s}_{ht}", from_mix=False)
            kb.value = 0.0
            if ht == CLOSE_HT:
                entry[s] = {"closing_key": True}
                continue
            sign = 1.0 if s == "r" else -1.0
            piv = rig.data.bones[f"upperarm_{s}"].head_local
            fixed = {}
            for v in rest:
                if v.co.x * sign < 0.03 or v.co.z < piv.z - Z_BELOW or (v.co - piv).length > RADIUS:
                    continue
                d = refs[ht][v.index] - P[v.index]
                if np.linalg.norm(d) * 1000 > MIN_MM:
                    fixed[v.index] = d
            ring = {i: 0 for i in fixed}
            frontier = list(fixed)
            for r in range(1, TAPER_RINGS + 1):
                nxt = []
                for i in frontier:
                    for j in adj[i]:
                        if j not in ring and rest[j].co.x * sign > 0.03:
                            ring[j] = r; nxt.append(j)
                frontier = nxt
            field = {i: fixed.get(i, np.zeros(3)) for i in ring}
            free = [i for i, r in ring.items() if r > 0 and r < TAPER_RINGS]
            for _ in range(60):
                for i in free:
                    nb = [field[j] for j in adj[i] if j in field]
                    field[i] = sum(nb) / len(nb)
            clipped, maxp, maxd = 0, 0.0, 0.0
            for i, dv in field.items():
                if np.linalg.norm(dv) < 1e-7:
                    continue
                maxp = max(maxp, float(np.linalg.norm(dv)))
                A = sum(x * mats[nm] for nm, x in W[i].items())
                U, sv, Vt = np.linalg.svd(A)
                dr = Vt.T @ np.diag(sv / (sv ** 2 + DAMP ** 2)) @ U.T @ dv
                L = float(np.linalg.norm(dr))
                if L > CAP_M:
                    dr *= CAP_M / L; clipped += 1
                maxd = max(maxd, min(L, CAP_M))
                kb.data[i].co = rest[i].co + Vector(dr)
            entry[s] = {"zone_vertices": len(fixed), "taper_vertices": len(free), "max_posed_mm": round(maxp * 1000, 1),
                        "max_rest_delta_mm": round(maxd * 1000, 1), "clipped": clipped,
                        "elevation_deg": round(angles[s][-1], 2)}
        log[str(ht)] = entry
    for s in SIDES:
        rig[f"hgpt_s3_angles_{s}"] = list(angles[s])
    bench._reset(rig)
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    return log



def main():
    """Dump the reference surfaces (run in its own process: the shoulder drive is installed once per process):
      python3.13 build_original_shape_target_corrective_blender.py -- --reference R5.blend --out refs.npz"""
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    get = lambda k: args[args.index(k) + 1]
    refs = reference_surfaces(get("--reference"), KEYS_HT)
    np.savez(get("--out"), **{str(k): v for k, v in refs.items()})


if __name__ == "__main__":
    main()
