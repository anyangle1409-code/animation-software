"""Shoulder root-cause diagnostic (14 Oct 2026; docs/CLAUDE_SHOULDER_DETACHED_ARM_ROOT_CAUSE_20261014.md). Diagnostic only."""
import pathlib as _pl
ROOT = str(_pl.Path(__file__).resolve().parents[2])
import sys, os, math
sys.path.insert(0, ROOT + "/scripts"); sys.path.insert(0, ROOT + "/scripts/anatomy_fit")
import bpy
from mathutils import Vector
ISB = os.environ.get("ISB") == "1"; AX = os.environ.get("AX", "1") == "1"
bpy.ops.wm.open_mainfile(filepath=ROOT + "/ORIGINAL_V1_WORK/anatomy/audit/HGPT_ANATOMICAL_AUDIT_r95_a003.blend")
import build_functional_shoulder_correction_blender as correction
import build_original_movement_benchmarks_blender as bench
import original_v1_review_candidate_drives as drives
import original_v1_scapula_isb_drive as isb
res = correction.build_corrected_scene(); rig, body = res["runtime"], res["body"]
for kb in body.data.shape_keys.key_blocks[1:]: kb.value = 0.0
if ISB: isb.install(res)
bench._reset(rig); V0, F = bench._evaluated(body); dom = bench.dominant_groups(body)
tag = f"isb{int(ISB)}ax{int(AX)}"
pb = rig.pose.bones
for ht in (0, 45, 90, 120, 145, 160):
    correction.apply_corrected_pose(res, ht, axial=AX)
    q = drives._rel_quat(rig, "upperarm_r", "scapula_r")
    arm = (pb["upperarm_r"].tail - pb["upperarm_r"].head).normalized()
    V, _ = bench._evaluated(body); m = bench.frame_metrics(V0, V, F, dom, min(v.z for v in V0))
    print("ISB", tag, ht, "HT", round(math.degrees(arm.angle(Vector((0, 0, -1)))), 1), "arm-vs-scap", round(math.degrees(min(q.angle, 2*math.pi-q.angle)), 1),
          "| c/s/p/vol", m["collapse_lt_0_1"], m["stretch_gt_2"], m["self_intersecting_pairs"], round(m["body_volume_change_pct"], 2),
          "| glenoid", [round(c*1000) for c in pb["upperarm_r"].head], "scap tail", [round(c*1000) for c in pb["scapula_r"].tail],
          "| mirror", round(abs(pb["upperarm_r"].head.x + pb["upperarm_l"].head.x)*1000, 2), round(abs(pb["scapula_r"].tail.z - pb["scapula_l"].tail.z)*1000, 2))
correction.apply_corrected_pose(res, 160, axial=AX)
sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"
for o in sc.objects:
    if o.type in ("MESH", "CURVE") and o is not body: o.hide_render = True
mat = bpy.data.materials.new("S"); mat.diffuse_color = (0.64, 0.46, 0.38, 1); body.data.materials.clear(); body.data.materials.append(mat)
sc.display.shading.color_type = "MATERIAL"; sc.display.shading.show_cavity = True
sc.render.resolution_x = sc.render.resolution_y = 600
cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cd.ortho_scale = 0.62
cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
t = pb["upperarm_r"].head.copy() + Vector((0, 0, 0.02))
for nm, d in (("front", (0, -1, 0)), ("rear", (0, 1, 0)), ("side", (1, 0, 0))):
    cam.location = t + Vector(d) * 3; cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = f"{sys.argv[-1]}/{tag}_{nm}.png"; bpy.ops.render.render(write_still=True)
