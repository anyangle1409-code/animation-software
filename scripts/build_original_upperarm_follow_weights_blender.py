#!/usr/bin/env python3
"""Upper-arm follow weights for ORIGINAL_v1 review candidates (Claude, 16 Oct 2026; review only; bpy).

Owner (on R29/R30, press frames t = 0.40 / 0.50 / 0.80): "there looks like there is a join here but there isn't.  The only
joint will be the elbow.  That bone should continue on into the shoulder not bend there."

Measured on R29 (scratch tool follow.py): the skin of the upper half of the upper arm is weighted mostly to the shoulder-cap
helper (half-follow), the upper spine (spine_02/03: 17 % over 25-55 % of the arm) and the pec / lat muscle-line helpers
(9 %), not the humerus - upperarm weight 0.23 / 0.39 / 0.59 / 0.79 over 20-30 / 30-40 / 40-50 /
50-60 % of the way from the shoulder joint to the elbow - so at every press elevation that skin lags 8-10 cm behind the
bone and the arm bends where the weighting changes, a third of the way down the upper arm.

This hands the cap / girdle share of upper-arm skin back to the humerus: along the rest arm axis, a vertex T0 below the
shoulder pivot keeps its weights, one T1 below follows the humerus completely (smoothstep between).  Only arm skin is changed
(within RADIUS of the rest arm axis, and not torso skin beside the arm: skin on the medial side of the axis whose normal faces
outwards is torso).  Upper-arm weight is only ever increased; total weight per vertex is kept; at most 4 influences.
Vertex positions, faces and shape keys are untouched.
  python3.13 build_original_upperarm_follow_weights_blender.py -- --blend R18.blend --out R18W.blend --report report.json
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

import bpy  # noqa: E402
import numpy as np  # noqa: E402

import original_v1_review_candidate_drives as drives  # noqa: E402

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
T0, T1 = (float(v) for v in os.environ.get("FOLLOW_T", "0.02,0.07").split(","))
RADIUS = float(os.environ.get("FOLLOW_RADIUS", 0.085))
GROUPS = tuple(os.environ.get("FOLLOW_GROUPS", "shoulder_cap,clavicle,scapula").split(","))
NAME = os.environ.get("FOLLOW_NAME", "R18W")
SIDES = ("l", "r")


def get(flag):
    return args[args.index(flag) + 1]


def main():
    import build_functional_shoulder_correction_blender as correction
    import build_original_movement_benchmarks_blender as bench
    import build_original_shoulder_relax_corrective_blender as s1
    import original_v1_press_extension as px
    blend, out, report = get("--blend"), Path(get("--out")), Path(get("--report"))
    if out.exists():
        raise FileExistsError(out)
    bpy.ops.wm.open_mainfile(filepath=str(Path(blend).resolve()))
    res = correction.build_corrected_scene()
    body, rig = res["body"], res["runtime"]
    drives.setup(res)
    px.install()
    bench._reset(rig)
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    V0, F = bench._evaluated(body)
    R = np.array([tuple(v) for v in V0]); Fa = np.array(F)
    Nf = np.cross(R[Fa[:, 1]] - R[Fa[:, 0]], R[Fa[:, 2]] - R[Fa[:, 0]])
    Nv = np.zeros_like(R)
    for c in range(3):
        np.add.at(Nv, Fa[:, c], Nf)
    Nv /= np.maximum(np.linalg.norm(Nv, axis=1)[:, None], 1e-15)
    W = rig.matrix_world
    me = body.data
    keys0 = {kb.name: np.array([tuple(d.co) for d in kb.data]) for kb in me.shape_keys.key_blocks}
    vg = body.vertex_groups
    log = {}
    for s in SIDES:
        sg = 1.0 if s == "r" else -1.0
        b = rig.data.bones[f"upperarm_{s}"]
        h0 = np.array(tuple(W @ b.head_local)); ax = np.array(tuple(W @ b.tail_local)) - h0; ax /= np.linalg.norm(ax)
        lat = np.array([sg, 0.0, 0.0]) - (sg * ax[0]) * ax; lat /= np.linalg.norm(lat)     # outward, across the arm
        rel = R - h0; t = rel @ ax; perp = rel - t[:, None] * ax; r = np.linalg.norm(perp, axis=1)
        dirn = perp / np.maximum(r[:, None], 1e-9)
        torso = ((dirn @ lat) < -0.3) & ((Nv @ lat) > 0.2)          # medial of the axis, facing outwards: torso beside the arm
        g = np.clip((t - T0) / (T1 - T0), 0, 1); g = g * g * (3 - 2 * g)
        # R31c: the inner (armpit-side) skin of the arm keeps its blend into the torso - handing it to the humerus too pushed
        # it into the chest with the arm down (keys-off benchmarks: walk 0 -> 10, grip 18 -> 126, push-up 0 -> 172 pairs);
        # the false joint the owner saw is on the outer / back edge, so only skin outside FOLLOW_MEDIAL (dir . lateral) moves
        outer = (dirn @ lat) > float(os.environ.get("FOLLOW_MEDIAL", -1.1))
        if os.environ.get("FOLLOW_MEDIAL_RAMP"):
            # R31d: a hard outer / inner cut stretched the skin between them (keys-off: push-up stretch 79 -> 207): ramp the
            # hand-over round the arm instead, none on the inner face (dir . lateral <= M0), full on the outer (>= M1)
            m0_, m1_ = (float(x) for x in os.environ["FOLLOW_MEDIAL_RAMP"].split(","))
            h_ = np.clip((dirn @ lat - m0_) / (m1_ - m0_), 0, 1); g = g * h_ * h_ * (3 - 2 * h_)
            outer = g > 0
        cand = np.where((g > 0) & (r < RADIUS) & ~torso & outer)[0]
        up = vg[f"upperarm_{s}"]
        donors = [vg[f"{n}_{s}"] if f"{n}_{s}" in vg else vg[n] for n in GROUPS if f"{n}_{s}" in vg or n in vg]   # spine_* are unsided
        donor_idx = {d.index for d in donors}
        changed, moved = 0, []
        for i in (int(x) for x in cand):
            v = me.vertices[i]
            ws = {e.group: e.weight for e in v.groups}
            share = sum(w for k, w in ws.items() if k in donor_idx)
            if share <= 1e-6:
                continue
            m = g[i] * share
            for k in donor_idx & set(ws):
                ws[k] *= (1.0 - g[i])
            ws[up.index] = ws.get(up.index, 0.0) + m
            total = sum(ws.values())
            # 4-influence limit.  R31 note: the R18Wg5 stage behind R31 trimmed to the top 4 regardless, which on 22 vertices
            # per side at the top of the shoulder (6 influences in R18) dropped the upperarm weight (by <= 0.032); keep it now
            others = sorted(((k, w) for k, w in ws.items() if k != up.index), key=lambda kv: -kv[1])
            keep = [(up.index, ws[up.index])] + others[:3] if ws[up.index] > 1e-6 else others[:4]
            ks = sum(w for _, w in keep)
            present = {e.group for e in v.groups}
            for k in ws:
                if k in present:
                    vg[k].remove([i])
            for k, w in keep:
                if w > 1e-6:
                    vg[k].add([i], w * total / ks, "REPLACE")
            changed += 1; moved.append(m)
        log[s] = {"changed_vertices": changed, "moved_weight_mean": round(float(np.mean(moved)) if moved else 0.0, 3),
                  "moved_weight_max": round(float(np.max(moved)) if moved else 0.0, 3), "torso_excluded": int(torso[(g > 0) & (r < RADIUS)].sum())}
        print("FOLLOW", s, log[s], flush=True)
    for kb in me.shape_keys.key_blocks:
        if not np.array_equal(np.array([tuple(d.co) for d in kb.data]), keys0[kb.name]):
            raise RuntimeError(f"shape key {kb.name} changed")
    bpy.context.scene["hgpt_upperarm_follow"] = True
    output = s1.save(res, out, blend, NAME)
    rep = {"kind": "ORIGINAL_V1_REVIEW_CANDIDATE_STAGE", "candidate": NAME, "status": "REVIEW_CANDIDATE_NOT_ACCEPTED",
           "approved": False, "stage": "upper-arm follow weights (cap / girdle share of upper-arm skin handed to the humerus)",
           "params": {"t0_m": T0, "t1_m": T1, "radius_m": RADIUS, "donor_groups": GROUPS, "medial_limit": float(os.environ.get("FOLLOW_MEDIAL", -1.1)), "medial_ramp": os.environ.get("FOLLOW_MEDIAL_RAMP", "")}, "log": log, "output": output}
    report.write_text(json.dumps(rep, indent=1) + "\n")


if __name__ == "__main__":
    main()
