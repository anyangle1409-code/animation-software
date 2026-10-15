#!/usr/bin/env python3
"""ORIGINAL_v1 review candidate R12 (Claude, 14 Oct 2026): R11 + S5 baked delta-mush shapes for the full-range press.
Owner: "Continue to fix the issue. We can't progress until it's fixed."  docs/CLAUDE_ORIGINAL_V1_REVIEW_CANDIDATE_R12_20261014.md.

Three steps, each in its own process (the shoulder drive installs once per process):

  1. --make-target: R11 with its S4 keys replaced by S4 re-solved on the re-meshed body at 5x (trapezius 0.3 of that) and a
     delta-mush deformer (Blender Corrective Smooth, 60 iterations, factor 1.0, length-weighted, rest = original
     coordinates) on the shoulder region (full within 16 cm of a glenohumeral pivot, cosine fade to 24 cm).  Review-only
     intermediate: its look is the goal, but live it pushes armpit skin through itself (start 50 / near top ~150 / lockout
     ~190 self-intersecting pairs), so it is never shipped.
       python3.13 build_original_review_candidate_r12_blender.py -- --make-target --blend R11.blend --out TARGET.blend
  2. --dump: the target's posed surfaces at the S5 key poses (build_original_bake_corrective_blender.dump_targets).
       python3.13 build_original_review_candidate_r12_blender.py -- --dump --blend TARGET.blend --out targets.npz
  3. --bake: R12 = R11 + HGPT_S5_BAKE_ keys (build_original_bake_corrective_blender.build, smooth guard along the press).
       python3.13 build_original_review_candidate_r12_blender.py -- --bake --blend R11.blend --targets targets.npz \
           --out R12.blend --report JSON
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from pathlib import Path

TARGET_ENV = {"S4_SCALE": "5.0", "S4_REGION_SCALE": "deltoid:1,armpit:1,trapezius:0.3"}
BAKE_ENV = {"S5_MASK_RINGS": "0", "S5_RESOLVE": "0", "S5_SMOOTH_GUARD": "1", "S5_POST_SMOOTH": "0"}
CS = {"iterations": 60, "factor": 1.0, "smooth_type": "LENGTH_WEIGHTED", "r0_m": 0.16, "r1_m": 0.24}
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
os.environ.update(TARGET_ENV if "--make-target" in args else BAKE_ENV)

import bpy  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

import original_v1_review_candidate_drives as drives  # noqa: E402


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def get(k):
    return args[args.index(k) + 1]


def make_target():
    import build_functional_shoulder_correction_blender as correction
    import build_original_movement_benchmarks_blender as bench
    import build_original_sculpt_corrective_blender as s4
    import original_v1_press_extension as px
    import original_v1_shoulder_cap_helper as cap
    bpy.ops.wm.open_mainfile(filepath=str(Path(get("--blend")).resolve()))
    body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
    for kb in [k for k in body.data.shape_keys.key_blocks if k.name.startswith(s4.PREFIX)]:
        body.shape_key_remove(kb)
    res = correction.build_corrected_scene()
    rig = res["runtime"]
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    drives.setup(res)
    px.install()
    s4.build(res)
    bench._reset(rig)
    cap.remove(rig)
    import original_v1_hip_crease_helper as hip                  # R13+: in-memory hip helpers (no-op for R12)
    hip.remove(rig)
    import original_v1_muscle_line_helpers as muscle             # R14+: in-memory muscle-line helpers (no-op for R12)
    muscle.remove(rig)
    g = body.vertex_groups.new(name="HGPT_CS_SHOULDER")
    for s in ("l", "r"):
        piv = rig.data.bones[f"upperarm_{s}"].head_local
        for v in body.data.vertices:
            d = (v.co - piv).length
            if d < CS["r1_m"]:
                w = 1.0 if d <= CS["r0_m"] else 0.5 * (1 + math.cos(math.pi * (d - CS["r0_m"]) / (CS["r1_m"] - CS["r0_m"])))
                g.add([v.index], w, "REPLACE")
    m = body.modifiers.new("HGPT_CS_SHOULDER", "CORRECTIVE_SMOOTH")
    m.vertex_group, m.iterations, m.factor = g.name, CS["iterations"], CS["factor"]
    m.smooth_type, m.rest_source, m.use_pin_boundary = CS["smooth_type"], "ORCO", False
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    bpy.ops.wm.save_as_mainfile(filepath=str(Path(get("--out")).resolve()), copy=True)


def dump():
    import build_original_bake_corrective_blender as s5
    s5.dump_targets(get("--blend"), get("--out"))


def bake():
    import numpy as np
    import build_functional_shoulder_correction_blender as correction
    import build_original_bake_corrective_blender as s5
    import build_original_movement_benchmarks_blender as bench
    import build_original_shoulder_relax_corrective_blender as s1
    import original_v1_press_extension as px
    parent, out, report = get("--blend"), Path(get("--out")), Path(get("--report"))
    if out.exists():
        raise FileExistsError(out)
    z = np.load(get("--targets"))
    targets = {k: z[k] for k in z.files}
    bpy.ops.wm.open_mainfile(filepath=str(Path(parent).resolve()))
    res = correction.build_corrected_scene()
    body, rig = res["body"], res["runtime"]
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    drives.setup(res)
    px.install()
    bench._reset(rig)
    V0, F = bench._evaluated(body)
    dom = bench.dominant_groups(body)
    floor = min(v.z for v in V0)
    log = s5.build(res, targets)

    def path(use):
        rows = []
        for t in tuple(i / 20 for i in range(21)):
            a = px.pose_press_full(res, t)
            drives.drive(rig, body)
            if not use:
                for kb in body.data.shape_keys.key_blocks:
                    if kb.name.startswith(s5.PREFIX):
                        kb.value = 0.0
            V, _ = bench._evaluated(body)
            m = bench.frame_metrics(V0, V, F, dom, floor)
            rows.append({"t": t, "ht": round(a["humerothoracic_elevation"], 2), "collapse": m["collapse_lt_0_1"],
                         "stretch": m["stretch_gt_2"], "pairs": m["self_intersecting_pairs"],
                         "volume_pct": m["body_volume_change_pct"]})
        bench._reset(rig)
        return rows
    before, after = path(False), path(True)
    for a, b in zip(before, after):
        print("R12P", a["t"], a["ht"], (a["collapse"], a["stretch"], a["pairs"], round(a["volume_pct"], 2)), "->",
              (b["collapse"], b["stretch"], b["pairs"], round(b["volume_pct"], 2)))
    output = s1.save(res, out, parent, "R12")
    rep = {"kind": "ORIGINAL_V1_REVIEW_CANDIDATE", "candidate": "R12", "status": "REVIEW_CANDIDATE_NOT_ACCEPTED", "approved": False,
           "target_recipe": {"s4_env": TARGET_ENV, "corrective_smooth": CS}, "bake_env": BAKE_ENV,
           "targets_sha256": sha(get("--targets")), "s5": {"keys_ht": s5.KEYS_HT, "log": log},
           "press_path_r11": before, "press_path_r12": after, "output": output}
    report.write_text(json.dumps(rep, indent=1, default=str) + "\n")


if __name__ == "__main__":
    if "--make-target" in args:
        make_target()
    elif "--dump" in args:
        dump()
    else:
        bake()
