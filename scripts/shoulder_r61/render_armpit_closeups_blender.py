"""Armpit close-ups of an unsaved study for the owner to mark (Claude, 20 Oct 2026).

Same immutable R41 model, installer (Claude's R61 copy: 166 deg control allowed) and press poses as the review renders.
For each press angle, the camera aims at the posed right shoulder joint from several viewpoints.  Nothing is saved.
  blender --background --python render_armpit_closeups_blender.py -- <R57 root> source.npz candidate.npz outdir
"""
from pathlib import Path
import sys, os, hashlib
import bpy, numpy as np
from mathutils import Vector

root, source, solution, out = sys.argv[-4:]
ROOT = Path(root).resolve()
sys.path[:0] = [str(Path(__file__).resolve().parent), str(ROOT / 'scripts'), str(ROOT / 'scripts/anatomy_fit')]
os.environ['S7_LOCKOUT_HT'] = '166'
import build_original_review_candidate_r17_blender as r17
import build_original_movement_benchmarks_blender as bench
import original_v1_review_candidate_drives as drives
import original_v1_press_extension as px
from claude_r61_native import install

out = Path(out); out.mkdir(parents=True, exist_ok=True)
model = ROOT / 'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017/HGPT_ORIGINAL_V1_REVIEW_R41_CODEX.blend'
if hashlib.sha256(model.read_bytes()).hexdigest() != '4c44b1fe14aeefd9a976f45baada60b4b81aaaa7cd736a300ca7cede2b0aaf2e':
    raise ValueError("Original Blender model bytes changed")
res = r17._setup(model)
rig, body = res['runtime'], res['body']
z = np.load(source)
install(res, np.load(solution)['dense_delta'], z['sampling_basis'])
scene = bpy.context.scene
for ob in scene.objects:
    if ob.type in ('MESH', 'CURVE') and ob is not body:
        ob.hide_render = True
mat = bpy.data.materials.new('REVIEW_ONLY'); mat.diffuse_color = (.72, .55, .45, 1)
body.data.materials.clear(); body.data.materials.append(mat)
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'; scene.display.shading.color_type = 'MATERIAL'; scene.display.shading.show_cavity = True
scene.render.film_transparent = True
scene.render.resolution_x = scene.render.resolution_y = 900
scene.render.image_settings.file_format = 'PNG'
cd = bpy.data.cameras.new('CLOSE'); cd.type = 'ORTHO'; cd.ortho_scale = 0.42
cam = bpy.data.objects.new('CLOSE', cd); scene.collection.objects.link(cam); scene.camera = cam
views = {"rear": (0.15, 1, 0.0), "rear_three_quarter": (0.75, 0.65, 0.05), "side": (1, 0.1, 0.0),
         "low_rear": (0.45, 0.8, -0.45), "front_three_quarter": (0.75, -0.65, 0.05)}
for t in (0.625, 0.7, 0.75, 0.8, 0.9, 1.0):
    bench._reset(rig); px.pose_press_full(res, t); drives.drive(rig, body); bpy.context.view_layer.update()
    k = t * t * (3 - 2 * t); ht = 70 + 96 * k
    target = rig.matrix_world @ rig.pose.bones['upperarm_r'].head + Vector((0.0, 0.0, -0.06))
    for view, d in views.items():
        d = Vector(d).normalized()
        cam.location = target + d * 3
        cam.rotation_mode = 'QUATERNION'; cam.rotation_quaternion = (-d).to_track_quat('-Z', 'Y')
        scene.render.filepath = str(out / f"armpit_{ht:05.1f}deg_{view}.png")
        bpy.ops.render.render(write_still=True)
    # R65: whole upper back from behind, framed like the owner's reference photos (head, both arms, waist)
    mid = (rig.matrix_world @ rig.pose.bones['upperarm_l'].head + rig.matrix_world @ rig.pose.bones['upperarm_r'].head) / 2
    d = Vector((0.0, 1.0, 0.0))
    cd.ortho_scale = 1.15
    cam.location = mid + Vector((0.0, 0.0, 0.05)) + d * 3
    cam.rotation_quaternion = (-d).to_track_quat('-Z', 'Y')
    scene.render.filepath = str(out / f"armpit_{ht:05.1f}deg_back_full.png")
    bpy.ops.render.render(write_still=True)
    cd.ortho_scale = 0.42
print('CLOSEUPS_DONE', flush=True)
