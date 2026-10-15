#!/usr/bin/env python3
"""ORIGINAL_v1 review candidate R13 (Claude, 15 Oct 2026): R12 + the hip-crease helper joint and H1 baked delta-mush hip
keys.  Owner: "Yes. Continue" (the hip fold with the shoulder recipe).  docs/CLAUDE_ORIGINAL_V1_REVIEW_CANDIDATE_R13_20261015.md.

Four steps, each in its own process (the review drives install once per process):

  1. --weights: R12 + hip-crease helper chain weights (original_v1_hip_crease_helper.assign_weights, HELPER parameters).
       python3.13 build_original_review_candidate_r13_blender.py -- --weights --blend R12.blend --out W.blend
  2. --make-target: W + a delta-mush deformer (Corrective Smooth, CS) on both hip regions.  Review-only intermediate:
     the look wanted, but live it adds lunge / single-leg self-intersections and is a new runtime deformer.
       python3.13 build_original_review_candidate_r13_blender.py -- --make-target --blend W.blend --out TARGET.blend
  3. --dump: the target's posed surfaces at the H1 key angles.
       python3.13 build_original_review_candidate_r13_blender.py -- --dump --blend TARGET.blend --out targets.npz
  4. --bake: R13 = W + HGPT_H1_BAKE_ keys (build_original_hip_bake_corrective_blender.build, smooth guard on the hip paths).
       python3.13 build_original_review_candidate_r13_blender.py -- --bake --blend W.blend --parent R12.blend \
           --targets targets.npz --out R13.blend --report JSON
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from pathlib import Path

HELPER = {"HIP_T": "-0.14,0.20", "HIP_FRACTION": "0.45", "HIP_FADE": "0.14,0.20"}
CS = {"iterations": 60, "factor": 1.0, "smooth_type": "LENGTH_WEIGHTED", "r0_m": 0.14, "r1_m": 0.22}
os.environ.update(HELPER)
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

import bpy  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

import original_v1_review_candidate_drives as drives  # noqa: E402

BODY = "HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def get(k):
    return args[args.index(k) + 1]


def _scene(path):
    import build_functional_shoulder_correction_blender as correction
    bpy.ops.wm.open_mainfile(filepath=str(Path(path).resolve()))
    res = correction.build_corrected_scene()
    for kb in res["body"].data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    return res


def _save_copy(out):
    out = Path(out)
    if out.exists():
        raise FileExistsError(out)
    bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()), copy=True)


def weights():
    import build_original_movement_benchmarks_blender as bench
    import original_v1_hip_crease_helper as hip
    import original_v1_shoulder_cap_helper as cap
    res = _scene(get("--blend"))
    body, rig = res["body"], res["runtime"]
    print("R13W", hip.assign_weights(body, rig))
    bench._reset(rig)
    cap.remove(rig)
    hip.remove(rig)
    _save_copy(get("--out"))


def make_target():
    bpy.ops.wm.open_mainfile(filepath=str(Path(get("--blend")).resolve()))
    body = bpy.data.objects[BODY]
    rig = body.find_armature()
    g = body.vertex_groups.new(name="HGPT_CS_HIP")
    for v in body.data.vertices:
        w = 0.0
        for s in ("l", "r"):
            d = (v.co - rig.data.bones[f"thigh_{s}"].head_local).length
            if d < CS["r1_m"]:
                w = max(w, 1.0 if d <= CS["r0_m"] else 0.5 * (1 + math.cos(math.pi * (d - CS["r0_m"]) / (CS["r1_m"] - CS["r0_m"]))))
        if w > 0:
            g.add([v.index], w, "REPLACE")
    m = body.modifiers.new("HGPT_CS_HIP", "CORRECTIVE_SMOOTH")
    m.vertex_group, m.iterations, m.factor = g.name, CS["iterations"], CS["factor"]
    m.smooth_type, m.rest_source, m.use_pin_boundary = CS["smooth_type"], "ORCO", False
    _save_copy(get("--out"))


def dump():
    import build_original_hip_bake_corrective_blender as h1
    h1.dump_targets(get("--blend"), get("--out"))


def bake():
    import numpy as np
    import build_original_hip_bake_corrective_blender as h1
    import build_original_movement_benchmarks_blender as bench
    import build_original_shoulder_relax_corrective_blender as s1
    wblend, parent, out, report = get("--blend"), get("--parent"), Path(get("--out")), Path(get("--report"))
    if out.exists():
        raise FileExistsError(out)
    z = np.load(get("--targets"))
    targets = {k: z[k] for k in z.files}
    res = _scene(wblend)
    body, rig = res["body"], res["runtime"]
    drives.setup(res)
    log = h1.build(res, targets)
    bench._reset(rig)
    output = s1.save(res, out, parent, "R13")
    output["weights_blend_sha256"] = sha(wblend)
    rep = {"kind": "ORIGINAL_V1_REVIEW_CANDIDATE", "candidate": "R13", "status": "REVIEW_CANDIDATE_NOT_ACCEPTED", "approved": False,
           "helper": HELPER, "target_corrective_smooth": CS, "targets_sha256": sha(get("--targets")),
           "h1": {"keys_deg": h1.KEYS_DEG, "guard_paths": h1.GUARD_PATHS, "log": log}, "output": output}
    report.write_text(json.dumps(rep, indent=1, default=str) + "\n")


if __name__ == "__main__":
    {"--weights": weights, "--make-target": make_target, "--dump": dump}.get(next((a for a in args if a in (
        "--weights", "--make-target", "--dump")), None), bake)()
