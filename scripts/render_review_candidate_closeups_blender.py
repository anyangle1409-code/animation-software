#!/usr/bin/env python3
"""Anatomical close-ups of an ORIGINAL_v1 blend at fixed review poses (bpy, Workbench; identical cameras per pose).

Poses: shoulder at 145 and 160 deg coupled elevation (front, rear, side), knee 110 deg (lateral), elbow 100 deg (lateral), closed fist
(side), standing foot (medial).  With --drives the R1 helper/K1 drives run after every pose.  Nothing is saved.

  python3.13 render_review_candidate_closeups_blender.py -- --blend B.blend --out DIR --tag NAME [--drives]
"""
from __future__ import annotations

import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    get = lambda k: args[args.index(k) + 1]
    bpy.ops.wm.open_mainfile(filepath=str(Path(get("--blend")).resolve()))
    out, tag, use_drives = Path(get("--out")), get("--tag"), "--drives" in args
    import build_functional_shoulder_correction_blender as correction
    import build_original_knee_contact_corrective_blender as k1
    import build_original_movement_benchmarks_blender as bench
    import original_v1_review_candidate_drives as drives
    res = correction.build_corrected_scene()
    body, rig = res["body"], res["runtime"]
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    scene = bpy.context.scene
    for o in scene.objects:
        if o.type in ("MESH", "CURVE") and o is not body:
            o.hide_render = True
    mat = bpy.data.materials.new("HGPT_CU_SKIN_TMP"); mat.diffuse_color = (0.64, 0.46, 0.38, 1.0)
    body.data.materials.clear(); body.data.materials.append(mat)
    scene.render.engine = "BLENDER_WORKBENCH"
    sh = scene.display.shading
    sh.light, sh.color_type, sh.show_cavity = "STUDIO", "MATERIAL", True
    scene.render.resolution_x = scene.render.resolution_y = 600
    scene.render.image_settings.file_format = "PNG"
    cd = bpy.data.cameras.new("HGPT_CU_CAM_TMP"); cd.type = "ORTHO"
    cam = bpy.data.objects.new("HGPT_CU_CAM_TMP", cd); scene.collection.objects.link(cam); scene.camera = cam
    out.mkdir(parents=True, exist_ok=True)

    def shoot(name, target, direction, scale):
        cd.ortho_scale = scale
        cam.location = target + Vector(direction).normalized() * 3.0
        cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(out / f"{tag}__{name}.png")
        bpy.ops.render.render(write_still=True)

    def finish():
        if use_drives:
            drives.drive(rig, body)
        bpy.context.view_layer.update()

    for ht in (145, 160):
        correction.apply_corrected_pose(res, ht); finish()
        c = rig.pose.bones["upperarm_r"].head.copy() + Vector((0, 0, 0.02))
        for view, d in (("front", (0, -1, 0)), ("rear", (0, 1, 0)), ("side", (1, 0, 0))):
            shoot(f"shoulder{ht}_{view}", c, d, 0.62)
    k1._pose_pure(rig, "knee", 110); finish()
    shoot("knee110_lateral", rig.pose.bones["shin_r"].head.copy(), (1, 0, 0), 0.55)
    k1._pose_pure(rig, "elbow", 100); finish()
    shoot("elbow100_lateral", rig.pose.bones["forearm_r"].head.copy(), (1, 0, 0), 0.45)
    bench._reset(rig); bench.pose_grip(rig, body, 1.0); finish()
    shoot("fist_side", rig.pose.bones["hand_r"].head.copy(), (1, 0, 0), 0.32)
    bench._reset(rig); finish()
    foot = rig.pose.bones["foot_r"].head.copy() + Vector((0, -0.06, -0.04))
    shoot("foot_medial", foot, (-1, 0, 0.0), 0.36)
    print("closeups", tag, "->", out)


if __name__ == "__main__":
    main()
