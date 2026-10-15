#!/usr/bin/env python3
"""ORIGINAL_v1 review candidate R19 (Claude, 15 Oct 2026): the shoulder/armpit mesh rebuild, stage 1 (R18: R15 with the
shoulder edges re-routed along the folds, build_original_shoulder_fold_flip_blender.py) with its press S5 shapes re-baked
on the new triangulation.  R15's S5 shapes were baked, and their guard was run, on the old triangles.  Steps:
  0. --base: R18 without its S4/S5 keys (everything else as R18: press path v4, weights, helpers, other correctives);
  1-3. --make-target / --dump / --bake: build_original_review_candidate_r14_blender's steps with PRESS_PATH v4, NAME R19.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_original_review_candidate_r14_blender as r14  # noqa: E402

r14.PRESS_PATH = "v4"
r14.NAME = "R19"


def base():
    import bpy
    import build_functional_shoulder_correction_blender as correction
    bpy.ops.wm.open_mainfile(filepath=str(Path(r14.get("--blend")).resolve()))
    res = correction.build_corrected_scene()
    body, rig = res["body"], res["runtime"]
    if bpy.context.scene.get("hgpt_press_path") != "v4" or not bpy.context.scene.get("hgpt_shoulder_fold_flip"):
        raise RuntimeError("R19's base must be R18 (press path v4, shoulder fold flip)")
    dropped = [kb.name for kb in body.data.shape_keys.key_blocks if kb.name.startswith(r14.DROP)]
    for n in dropped:
        body.shape_key_remove(body.data.shape_keys.key_blocks[n])
    for s in ("l", "r"):
        for prop in ("hgpt_s4_angles", "hgpt_s5_angles"):
            if f"{prop}_{s}" in rig:
                del rig[f"{prop}_{s}"]
    out = Path(r14.get("--out"))
    if out.exists():
        raise FileExistsError(out)
    bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()), copy=True)
    print("R19BASE dropped", len(dropped), "keys")


if __name__ == "__main__":
    if "--base" in r14.args:
        base()
    elif "--make-target" in r14.args:
        r14.r12.make_target()
    elif "--dump" in r14.args:
        r14.r12.dump()
    else:
        r14.bake()
