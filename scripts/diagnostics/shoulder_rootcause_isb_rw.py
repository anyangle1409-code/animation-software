"""Shoulder root-cause diagnostic (14 Oct 2026; docs/CLAUDE_SHOULDER_DETACHED_ARM_ROOT_CAUSE_20261014.md). Diagnostic only."""
import pathlib as _pl
ROOT = str(_pl.Path(__file__).resolve().parents[2])
import sys, os, math
sys.path.insert(0, ROOT + "/scripts"); sys.path.insert(0, ROOT + "/scripts/anatomy_fit")
import bpy
from mathutils import Vector
R0, R1 = float(os.environ.get("R0", "0.10")), float(os.environ.get("R1", "0.18"))
bpy.ops.wm.open_mainfile(filepath=ROOT + "/ORIGINAL_V1_WORK/anatomy/audit/HGPT_ANATOMICAL_AUDIT_r95_a003.blend")
import build_functional_shoulder_correction_blender as correction
import build_original_movement_benchmarks_blender as bench
import original_v1_review_candidate_drives as drives
import original_v1_scapula_isb_drive as isb
res = correction.build_corrected_scene(); rig, body = res["runtime"], res["body"]
for kb in body.data.shape_keys.key_blocks[1:]: kb.value = 0.0
isb.install(res)
names = {g.index: g.name for g in body.vertex_groups}; G = body.vertex_groups
moved = 0
for s in ("r", "l"):
    ac = rig.data.bones[f"clavicle_{s}"].tail_local
    for v in body.data.vertices:
        w = {names[g.group]: g.weight for g in v.groups}
        ws = w.get(f"scapula_{s}", 0.0)
        if ws <= 0: continue
        d = (v.co - ac).length
        t = 0.0 if d <= R0 else 1.0 if d >= R1 else (lambda u: u*u*(3-2*u))((d - R0) / (R1 - R0))
        if t <= 0: continue
        take = ws * t
        G[f"scapula_{s}"].add([v.index], ws - take, "REPLACE")
        tgt = "spine_03" if "spine_03" in w or "spine_02" not in w else "spine_02"
        G[tgt].add([v.index], w.get(tgt, 0.0) + take, "REPLACE")
        moved += 1
bench._reset(rig); V0, F = bench._evaluated(body); dom = bench.dominant_groups(body)
tag = f"rw{int(R0*100)}_{int(R1*100)}"
print("RW", tag, "vertices reweighted", moved)
pb = rig.pose.bones
for ht in (90, 120, 145, 160):
    correction.apply_corrected_pose(res, ht)
    q = drives._rel_quat(rig, "upperarm_r", "scapula_r")
    V, _ = bench._evaluated(body); m = bench.frame_metrics(V0, V, F, dom, min(v.z for v in V0))
    print("RW", tag, ht, "c/s/p/vol", m["collapse_lt_0_1"], m["stretch_gt_2"], m["self_intersecting_pairs"], round(m["body_volume_change_pct"], 2))
correction.apply_corrected_pose(res, 160)
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
