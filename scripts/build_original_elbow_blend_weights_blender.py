#!/usr/bin/env python3
"""Elbow blend weights for ORIGINAL_v1 review candidates (Claude, 16 Oct 2026; review only; bpy).

Owner (on R31 press frames, arm elevation 132 / 145 deg, elbow 49 / 30 deg): "the bend at the elbow is too sharp and not
subtle at all".

Measured on B5 (the R31 base): along the arm, the arm skin's upper-arm share falls 0.83 -> 0.60 -> 0.39 -> 0.16 -> 0.05 at
-4 / -2 / 0 / +2 / +4 cm from the elbow joint - the whole hand-over from the humerus to the forearm happens within about 3 cm
either side of the joint, so a bent elbow makes a corner.

This spreads the hand-over: within ELBOW_W cm of the joint (measured along the upper arm above it and along the forearm
below it, from the rest bones), the arm share of each vertex (upperarm + forearm bones) is split again by a smoothstep from
all upper arm at -ELBOW_W (+ ELBOW_C) to all forearm at +ELBOW_W (+ ELBOW_C).  The forearm part keeps the vertex's own split
between the forearm / twist bones (or goes to the first forearm twist bone if it had none).  Skin whose weight is not almost
all arm (torso beside the elbow at rest) is left alone; other bones' weights are kept; positions, faces and shape keys are
untouched.
  python3.13 build_original_elbow_blend_weights_blender.py -- --blend in.blend --out out.blend --report report.json
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

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
HALF = float(os.environ.get("ELBOW_W", 7.0)) / 100          # half-width of the hand-over (m)
CENTRE = float(os.environ.get("ELBOW_C", -1.0)) / 100       # centre offset from the joint (m; measured centre about -1 cm)
RADIUS = float(os.environ.get("ELBOW_RADIUS", 0.07))
ARM_MIN = float(os.environ.get("ELBOW_ARM_MIN", 0.9))       # only vertices whose weight is at least this share arm
NAME = os.environ.get("ELBOW_NAME", "ELB")
SIDES = ("l", "r")


def get(flag):
    return args[args.index(flag) + 1]


def main():
    import build_functional_shoulder_correction_blender as correction
    import build_original_shoulder_relax_corrective_blender as s1
    blend, out, report = get("--blend"), Path(get("--out")), Path(get("--report"))
    if out.exists():
        raise FileExistsError(out)
    bpy.ops.wm.open_mainfile(filepath=str(Path(blend).resolve()))
    res = correction.build_corrected_scene()
    body = res["body"]
    rig = body.find_armature()
    me = body.data
    keys0 = {kb.name: np.array([tuple(d.co) for d in kb.data]) for kb in me.shape_keys.key_blocks}
    Wr, Mb = rig.matrix_world, body.matrix_world
    P = np.array([tuple(Mb @ v.co) for v in me.vertices])
    vg = body.vertex_groups
    log = {}
    for s in SIDES:
        up = vg[f"upperarm_{s}"].index
        fore = [vg[n].index for n in (f"forearm_{s}", f"forearm_tw0_{s}", f"forearm_tw1_{s}") if n in vg]
        default_fore = vg[f"forearm_tw0_{s}"].index if f"forearm_tw0_{s}" in vg else vg[f"forearm_{s}"].index
        gh = np.array(tuple(Wr @ rig.data.bones[f"upperarm_{s}"].head_local))
        el = np.array(tuple(Wr @ rig.data.bones[f"forearm_{s}"].head_local))
        au = (el - gh) / np.linalg.norm(el - gh)
        wr = np.array(tuple(Wr @ rig.data.bones[f"forearm_tw1_{s}"].tail_local if f"forearm_tw1_{s}" in rig.data.bones else Wr @ rig.data.bones[f"forearm_{s}"].tail_local))
        af = (wr - el) / np.linalg.norm(wr - el)
        rel = P - el
        t = np.where(rel @ au < 0, rel @ au, rel @ af)                      # signed distance from the joint along the arm
        axis = np.where((rel @ au < 0)[:, None], au, af)
        r = np.linalg.norm(rel - (rel * axis).sum(1)[:, None] * axis, axis=1)
        x = np.clip((t - CENTRE + HALF) / (2 * HALF), 0, 1)
        f_up = 1 - x * x * (3 - 2 * x)                                     # new upper-arm fraction of the arm share
        cand = np.where((np.abs(t - CENTRE) < HALF + 0.01) & (r < RADIUS))[0]
        changed, delta = 0, []
        for i in (int(c) for c in cand):
            v = me.vertices[i]
            ws = {e.group: e.weight for e in v.groups}
            total = sum(ws.values())
            arm = ws.get(up, 0.0) + sum(ws.get(k, 0.0) for k in fore)
            if total <= 0 or arm < ARM_MIN * total:
                continue
            fsum = sum(ws.get(k, 0.0) for k in fore)
            split = {k: ws.get(k, 0.0) / fsum for k in fore} if fsum > 1e-9 else {default_fore: 1.0}
            new_up = arm * f_up[i]
            delta.append(new_up - ws.get(up, 0.0))
            ws[up] = new_up
            for k in fore:
                ws.pop(k, None)
            for k, sp in split.items():
                ws[k] = arm * (1 - f_up[i]) * sp
            keep = sorted(ws.items(), key=lambda kv: -kv[1])[:4]
            ks = sum(w for _, w in keep)
            for e in list(v.groups):
                vg[e.group].remove([i])
            for k, w in keep:
                if w > 1e-6:
                    vg[k].add([i], w * total / ks, "REPLACE")
            changed += 1
        d = np.array(delta) if delta else np.zeros(1)
        log[s] = {"changed_vertices": changed, "upperarm_weight_change_min": round(float(d.min()), 3), "upperarm_weight_change_max": round(float(d.max()), 3)}
        print("ELBOW", s, log[s], flush=True)
    for kb in me.shape_keys.key_blocks:
        if not np.array_equal(np.array([tuple(d.co) for d in kb.data]), keys0[kb.name]):
            raise RuntimeError(f"shape key {kb.name} changed")
    bpy.context.scene["hgpt_elbow_blend"] = True
    output = s1.save(res, out, blend, NAME)
    rep = {"kind": "ORIGINAL_V1_REVIEW_CANDIDATE_STAGE", "candidate": NAME, "status": "REVIEW_CANDIDATE_NOT_ACCEPTED",
           "approved": False, "stage": "elbow blend weights (upper-arm / forearm hand-over spread along the arm)",
           "params": {"half_width_m": HALF, "centre_m": CENTRE, "radius_m": RADIUS, "arm_min_share": ARM_MIN}, "log": log, "output": output}
    report.write_text(json.dumps(rep, indent=1) + "\n")


if __name__ == "__main__":
    main()
