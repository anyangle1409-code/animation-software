#!/usr/bin/env python3
"""ORIGINAL_v1 review candidate R14 (Claude, 15 Oct 2026): R13 on press path v2 with the press-specific shoulder shapes
re-made along it.  Owner: "I want you to fix the shoulder press first ... When it gets to the highest point that is the worst
deformation", then a 7-view reference photo series and an armpit close-up.  docs/CLAUDE_ORIGINAL_V1_REVIEW_CANDIDATE_R14_20261015.md.

R13's S4 (sculpt) and S5 (baked delta mush) keys were made along press path v1 (arms 40 deg forward, forearms leaning in):
on path v2 (scripts/original_v1_press_extension.py: plane 15 deg, start 70 deg / elbow 140 deg, dumbbells by the ears) they
no longer fit, so R14 = R13 - S4 - S5 + scene["hgpt_press_path"] = "v2" + S4/S5 re-made with the R12 recipe along v2.
Steps, each in its own process:

  0. --base: R13 without its S4/S5 keys, flagged v2, with the neck-to-shoulder weight gradient
     (original_v1_shoulder_trap_weights: the top of the shoulder rises with the girdle instead of forming a shelf) and the
     pectoralis / latissimus muscle-line helper joints with their weights (original_v1_muscle_line_helpers: the front and
     back armpit folds stretch along the muscles).
       python3.13 build_original_review_candidate_r14_blender.py -- --base --blend R13.blend --out BASE.blend
  1. --make-target, 2. --dump: as build_original_review_candidate_r12_blender (S4 x5, trapezius 0.3, delta mush), on BASE.
  3. --bake: R14 = BASE + S5 keys baked from the targets (smooth guard along the v2 press).
       python3.13 build_original_review_candidate_r14_blender.py -- --bake --blend BASE.blend --parent R13.blend \
           --targets targets.npz --out R14.blend --report JSON
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

import build_original_review_candidate_r12_blender as r12  # noqa: E402  (sets the S4 / S5 recipe env from the step flag)
import os  # noqa: E402

import bpy  # noqa: E402

# target recipe on v2: R12's S4 (x5, trapezius 0.3) but a wider, shallower armpit vault - the owner's close-up shows a long
# soft hollow; R12's 7 cm vault at x5 leaves a taut ridge from the armpit to the collarbone on the v2 path
R14_TARGET_ENV = {"S4_REGION_SCALE": os.environ.get("R14_S4_REGION_SCALE", "deltoid:1,armpit:0.3,trapezius:0.3"),
                  "S4_AX_R": os.environ.get("R14_S4_AX_R", "0.12")}
if "--make-target" in sys.argv:
    os.environ.update(R14_TARGET_ENV)

args, get = r12.args, r12.get
PRESS_PATH = "v2"
NAME = "R14"                 # R15 re-uses these steps with PRESS_PATH = "v4"
EXTRA_RIG_PROPS = {}
DROP = ("HGPT_S4_SCULPT_", "HGPT_S5_BAKE_")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def base():
    import build_functional_shoulder_correction_blender as correction
    import build_original_movement_benchmarks_blender as bench
    import original_v1_hip_crease_helper as hip
    import original_v1_review_candidate_drives as drives
    import original_v1_shoulder_cap_helper as cap
    import original_v1_muscle_line_helpers as muscle
    import original_v1_shoulder_trap_weights as trap
    bpy.ops.wm.open_mainfile(filepath=str(Path(get("--blend")).resolve()))
    res = correction.build_corrected_scene()
    body, rig = res["body"], res["runtime"]
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    rig["hgpt_muscle_lines"] = {}                                # installs the muscle-line helpers in drives.setup
    drives.setup(res)
    print("R14BASE trap gradient", trap.assign_weights(body, rig))
    print("R14BASE muscle lines", muscle.assign_weights(body, rig))
    bench._reset(rig)
    cap.remove(rig)
    hip.remove(rig)
    muscle.remove(rig)
    dropped = [kb.name for kb in body.data.shape_keys.key_blocks if kb.name.startswith(DROP)]
    for n in dropped:
        body.shape_key_remove(body.data.shape_keys.key_blocks[n])
    for s in ("l", "r"):
        for prop in ("hgpt_s4_angles", "hgpt_s5_angles"):
            if f"{prop}_{s}" in rig:
                del rig[f"{prop}_{s}"]
    bpy.context.scene["hgpt_press_path"] = PRESS_PATH
    for k, v in EXTRA_RIG_PROPS.items():                       # R16: hgpt_cap_fraction_ramp
        rig[k] = v
    out = Path(get("--out"))
    if out.exists():
        raise FileExistsError(out)
    bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()), copy=True)
    print("R14BASE dropped", len(dropped), "keys")


def bake():
    import numpy as np
    import build_functional_shoulder_correction_blender as correction
    import build_original_bake_corrective_blender as s5
    import build_original_movement_benchmarks_blender as bench
    import build_original_shoulder_relax_corrective_blender as s1
    import original_v1_press_extension as px
    import original_v1_review_candidate_drives as drives
    blend, parent, out, report = get("--blend"), get("--parent"), Path(get("--out")), Path(get("--report"))
    if out.exists():
        raise FileExistsError(out)
    z = np.load(get("--targets"))
    targets = {k: z[k] for k in z.files}
    bpy.ops.wm.open_mainfile(filepath=str(Path(blend).resolve()))
    res = correction.build_corrected_scene()
    body, rig = res["body"], res["runtime"]
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    drives.setup(res)
    px.install()
    if px._PATH["name"] != PRESS_PATH:
        raise RuntimeError(f"the {NAME} base must be on press path {PRESS_PATH}")
    bench._reset(rig)
    V0, F = bench._evaluated(body)
    dom = bench.dominant_groups(body)
    floor = min(v.z for v in V0)
    # guard along the v2 press AND the shoulder-press benchmark's own coupled path (40 deg plane, to 160 deg): guarding the
    # v2 press alone left 190 pairs on the benchmark path
    import original_v1_shoulder_r4 as r4

    def benchmark_press(t):                 # the benchmark's own path: without the press-extension hook (which would turn
        hook = r4._S.get("extend")           # it into the v2 plane, as in the validation process, where it is not installed)
        r4._S["extend"] = None
        try:
            bench.pose_press(res, t, correction)
        finally:
            r4._S["extend"] = hook
    log = s5.build(res, targets, extra_guard_paths=[("benchmark_press", benchmark_press)])

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
            rows.append({"t": t, "ht": round(a["humerothoracic_elevation"], 2), "elbow": round(a["elbow_flexion"], 2),
                         "collapse": m["collapse_lt_0_1"], "stretch": m["stretch_gt_2"], "pairs": m["self_intersecting_pairs"],
                         "volume_pct": m["body_volume_change_pct"]})
        bench._reset(rig)
        return rows
    before, after = path(False), path(True)
    for a, b in zip(before, after):
        print("R14P", a["t"], a["ht"], (a["collapse"], a["stretch"], a["pairs"], round(a["volume_pct"], 2)), "->",
              (b["collapse"], b["stretch"], b["pairs"], round(b["volume_pct"], 2)))
    output = s1.save(res, out, parent, NAME)
    output["base_blend_sha256"] = sha(blend)
    rep = {"kind": "ORIGINAL_V1_REVIEW_CANDIDATE", "candidate": NAME, "status": "REVIEW_CANDIDATE_NOT_ACCEPTED", "approved": False,
           "press_path": PRESS_PATH, "press_path_params": px.PATHS[PRESS_PATH], "extra_rig_props": EXTRA_RIG_PROPS, "dropped_families": DROP,
           "target_recipe": {"s4_env": {**r12.TARGET_ENV, **R14_TARGET_ENV}, "corrective_smooth": r12.CS}, "bake_env": r12.BAKE_ENV,
           "targets_sha256": sha(get("--targets")), "s5": {"keys_ht": s5.KEYS_HT, "log": log},
           "press_path_without_s5": before, "press_path_r14": after, "output": output}
    report.write_text(json.dumps(rep, indent=1, default=str) + "\n")


if __name__ == "__main__":
    if "--base" in args:
        base()
    elif "--make-target" in args:
        r12.make_target()
    elif "--dump" in args:
        r12.dump()
    else:
        bake()
