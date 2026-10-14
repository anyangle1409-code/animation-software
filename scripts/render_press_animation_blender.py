#!/usr/bin/env python3
"""Shoulder-press animation frames of an ORIGINAL_v1 blend (bpy, Workbench, plain skin; identical cameras for every blend).

The benchmark press path (build_original_movement_benchmarks_blender.pose_press: humerothoracic elevation 90 -> 160 deg,
elbow 90 -> 0 deg) is sampled up and back down; with --drives the blend's review drives (drives.setup once, drives.drive
every frame) run, as in the validation.  Front, back and side views per frame.  Nothing is saved.

  python3.13 render_press_animation_blender.py -- --blend B.blend --out DIR --tag NAME [--drives] [--steps 20]

With --poses "ht:elbow,..." it renders those (humerothoracic elevation, elbow flexion) poses instead (front view + a front
close-up of the runtime _l shoulder = anatomical right, F-SIDE-001), e.g. to match reference photos; "ht:elbow:shrug" items
and --full use the full-range press (scripts/original_v1_press_extension.py: to 172 deg, lockout shrug).
"""
from __future__ import annotations

import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

VIEWS = (("front", (0, -1, 0)), ("back", (0, 1, 0)), ("side", (1, 0, 0)))
TARGET = Vector((0.0, 0.0, 1.72))
SCALE = 1.45


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    get = lambda k: args[args.index(k) + 1]
    bpy.ops.wm.open_mainfile(filepath=str(Path(get("--blend")).resolve()))
    out, tag, use_drives = Path(get("--out")), get("--tag"), "--drives" in args
    steps = int(get("--steps")) if "--steps" in args else 20
    import build_functional_shoulder_correction_blender as correction
    import build_original_movement_benchmarks_blender as bench
    import original_v1_review_candidate_drives as drives
    res = correction.build_corrected_scene()
    body, rig = res["body"], res["runtime"]
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    if use_drives:
        drives.setup(res)
    full = "--full" in args
    if full:
        import original_v1_press_extension as px
        px.install()
    bench._reset(rig)
    scene = bpy.context.scene
    for o in scene.objects:
        if o.type in ("MESH", "CURVE") and o is not body:
            o.hide_render = True
    mat = bpy.data.materials.new("HGPT_PRESS_SKIN_TMP"); mat.diffuse_color = (0.64, 0.46, 0.38, 1.0)
    body.data.materials.clear(); body.data.materials.append(mat)
    scene.render.engine = "BLENDER_WORKBENCH"
    sh = scene.display.shading
    sh.light, sh.color_type, sh.show_cavity = "STUDIO", "MATERIAL", True
    scene.render.resolution_x = scene.render.resolution_y = 480
    scene.render.image_settings.file_format = "PNG"
    cd = bpy.data.cameras.new("HGPT_PRESS_CAM_TMP"); cd.type = "ORTHO"; cd.ortho_scale = SCALE
    cam = bpy.data.objects.new("HGPT_PRESS_CAM_TMP", cd); scene.collection.objects.link(cam); scene.camera = cam
    out.mkdir(parents=True, exist_ok=True)
    if "--poses" in args:
        for n, item in enumerate(get("--poses").split(",")):
            vals = [float(x) for x in item.split(":")]
            ht, elbow, shrug = vals[0], vals[1], (vals[2] if len(vals) > 2 else 0.0)
            bench._reset(rig)
            if full:
                px.apply_pose(res, ht, shrug)
            else:
                correction.apply_corrected_pose(res, ht)
            for s in ("l", "r"):
                bench._rot(rig.pose.bones[f"forearm_{s}"], x=-elbow)
            bpy.context.view_layer.update()
            if use_drives:
                drives.drive(rig, body)
            bpy.context.view_layer.update()
            sh_c = rig.pose.bones["upperarm_l"].head.copy() + Vector((0, 0, -0.03))
            for view, target, scale in (("front", TARGET, SCALE), ("shoulder", sh_c, 0.50)):
                cd.ortho_scale = scale
                cam.location = target + Vector((0, -1, 0)) * 4.0
                cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
                scene.render.filepath = str(out / f"{tag}__pose{n}_{view}.png")
                bpy.ops.render.render(write_still=True)
        print("POSES", tag, "->", out)
        return
    ts = [i / steps for i in range(steps + 1)] + [i / steps for i in range(steps - 1, 0, -1)]   # up, then down
    for n, t in enumerate(ts):
        if full:
            px.pose_press_full(res, t)
        else:
            bench.pose_press(res, t, correction)
        if use_drives:
            drives.drive(rig, body)
        bpy.context.view_layer.update()
        for view, d in VIEWS:
            cam.location = TARGET + Vector(d).normalized() * 4.0
            cam.rotation_euler = (TARGET - cam.location).to_track_quat("-Z", "Y").to_euler()
            scene.render.filepath = str(out / f"{tag}__{n:03d}_{view}.png")
            bpy.ops.render.render(write_still=True)
    print("PRESS", tag, len(ts), "frames ->", out)


if __name__ == "__main__":
    main()
