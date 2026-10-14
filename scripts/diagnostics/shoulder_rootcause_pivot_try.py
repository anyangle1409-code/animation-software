"""Shoulder root-cause diagnostic (14 Oct 2026; docs/CLAUDE_SHOULDER_DETACHED_ARM_ROOT_CAUSE_20261014.md). Diagnostic only."""
import pathlib as _pl
ROOT = str(_pl.Path(__file__).resolve().parents[2])
import sys, os
sys.path.insert(0, ROOT + "/scripts"); sys.path.insert(0, ROOT + "/scripts/anatomy_fit")
import bpy
from mathutils import Vector
DROP = float(os.environ.get("DROP", "0")) / 1000
bpy.ops.wm.open_mainfile(filepath=ROOT + "/ORIGINAL_V1_WORK/anatomy/audit/HGPT_ANATOMICAL_AUDIT_r95_a003.blend")
import build_functional_shoulder_correction_blender as correction
import build_original_movement_benchmarks_blender as bench
res = correction.build_corrected_scene(); rig, body = res["runtime"], res["body"]
for kb in body.data.shape_keys.key_blocks[1:]: kb.value = 0.0
if DROP:
    v = bpy.context.view_layer
    for o in v.objects: o.select_set(False)
    v.objects.active = rig; rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    for s in ("l", "r"):
        rig.data.edit_bones[f"upperarm_{s}"].head.z -= DROP
    bpy.ops.object.mode_set(mode="OBJECT")
bench._reset(rig); V0, F = bench._evaluated(body); dom = bench.dominant_groups(body)
for ht in (90, 145, 160):
    correction.apply_corrected_pose(res, ht)
    V, _ = bench._evaluated(body); m = bench.frame_metrics(V0, V, F, dom, min(v.z for v in V0))
    print("PV", int(DROP*1000), ht, m["collapse_lt_0_1"], m["stretch_gt_2"], m["self_intersecting_pairs"], round(m["body_volume_change_pct"], 2))
if os.environ.get("REN"):
    correction.apply_corrected_pose(res, 160)
    sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"
    for o in sc.objects:
        if o.type in ("MESH", "CURVE") and o is not body: o.hide_render = True
    mat = bpy.data.materials.new("S"); mat.diffuse_color = (0.64, 0.46, 0.38, 1); body.data.materials.clear(); body.data.materials.append(mat)
    sc.display.shading.color_type = "MATERIAL"; sc.display.shading.show_cavity = True
    sc.render.resolution_x = sc.render.resolution_y = 600
    cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cd.ortho_scale = 0.62
    cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
    t = rig.pose.bones["upperarm_r"].head.copy() + Vector((0, 0, 0.02))
    for nm, d in (("front", (0, -1, 0)), ("rear", (0, 1, 0))):
        cam.location = t + Vector(d) * 3; cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = f"{os.environ['REN']}/drop{int(DROP*1000)}_{nm}.png"; bpy.ops.render.render(write_still=True)
