"""Render one unsaved S7 study (R52 or R59) through the whole press, for the owner's visual review (Claude, 20 Oct 2026).

Same immutable R41 model, installer, press pose and protection check as render_original_review_r57_local_blender.py
(pinned R57 sources), but a frame sequence (rear and three-quarter views) instead of three stills.  Nothing is saved.
  blender --background --python render_press_sequence_blender.py -- <R57 root> source.npz solution.npz outdir label frames
"""
from pathlib import Path
import sys, os, hashlib
import bpy, numpy as np
from mathutils import Vector

root, source, solution, out, label, frames = sys.argv[-6:]
ROOT = Path(root).resolve()
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/anatomy_fit')]
os.environ['S7_LOCKOUT_HT'] = '166'
import build_original_review_candidate_r17_blender as r17
import build_original_movement_benchmarks_blender as bench
import original_v1_review_candidate_drives as drives
import original_v1_press_extension as px
from original_review_r52_native import install

out = Path(out) / label
out.mkdir(parents=True, exist_ok=True)
model = ROOT / 'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017/HGPT_ORIGINAL_V1_REVIEW_R41_CODEX.blend'
expected = '4c44b1fe14aeefd9a976f45baada60b4b81aaaa7cd736a300ca7cede2b0aaf2e'
if hashlib.sha256(model.read_bytes()).hexdigest() != expected:
    raise ValueError("Original Blender model bytes changed")
res = r17._setup(model)
rig, body = res['runtime'], res['body']
keys = body.data.shape_keys.key_blocks
digest = lambda a: hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def protect():
    return dict(weights=[[(g.group, g.weight) for g in v.groups] for v in body.data.vertices],
                basis=digest(np.array([tuple(v.co) for v in keys[0].data])),
                non_s7={k.name: digest(np.array([tuple(v.co) for v in k.data])) for k in keys if not k.name.startswith('HGPT_S7_DELT_')})


before = protect()
z = np.load(source)
install(res, np.load(solution)['dense_delta'], z['sampling_basis'])
if protect() != before:
    raise RuntimeError("installer modified protected components")
scene = bpy.context.scene
for ob in scene.objects:
    if ob.type in ('MESH', 'CURVE') and ob is not body:
        ob.hide_render = True
mat = bpy.data.materials.new('REVIEW_ONLY'); mat.diffuse_color = (.72, .55, .45, 1)
body.data.materials.clear(); body.data.materials.append(mat)
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'; scene.display.shading.color_type = 'MATERIAL'; scene.display.shading.show_cavity = True
scene.render.film_transparent = True
scene.render.resolution_x = scene.render.resolution_y = 640
scene.render.image_settings.file_format = 'PNG'
cd = bpy.data.cameras.new('REVIEW'); cd.type = 'ORTHO'; cd.ortho_scale = 1.25
cam = bpy.data.objects.new('REVIEW', cd); scene.collection.objects.link(cam); scene.camera = cam
views = dict(rear=(0, 1, .02), three_quarter=(.7, .7, .05))
n = int(frames)
for i in range(n + 1):
    t = i / n
    bench._reset(rig); px.pose_press_full(res, t); drives.drive(rig, body); bpy.context.view_layer.update()
    for view, d in views.items():
        d = Vector(d).normalized()
        cam.location = Vector((0, 0, 1.5)) + d * 4
        cam.rotation_mode = 'QUATERNION'; cam.rotation_quaternion = (-d).to_track_quat('-Z', 'Y')
        scene.render.filepath = str(out / f'f{i:03d}_{view}.png')
        bpy.ops.render.render(write_still=True)
if hashlib.sha256(model.read_bytes()).hexdigest() != expected:
    raise RuntimeError("Immutable Blender model modified")
print('PRESS_SEQUENCE_COMPLETE', label, n + 1, flush=True)
