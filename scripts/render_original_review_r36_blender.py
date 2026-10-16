"""Render raw review skin at identical press times. No model changes are saved."""
import json
import sys
from pathlib import Path
import bpy
from mathutils import Vector
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "scripts/anatomy_fit")]
import build_functional_shoulder_correction_blender as correction
import build_original_movement_benchmarks_blender as bench
import original_v1_review_candidate_drives as drives
import original_v1_press_extension as px
args = sys.argv[sys.argv.index("--") + 1:]
model, out = Path(args[0]), Path(args[1])
out.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(model.resolve()))
res = correction.build_corrected_scene()
body, rig = res["body"], res["runtime"]
for kb in body.data.shape_keys.key_blocks[1:]:
    kb.value = 0
drives.setup(res)
px.install()
scene = bpy.context.scene
for obj in scene.objects:
    if obj.type in ("MESH", "CURVE") and obj is not body:
        obj.hide_render = True
material = bpy.data.materials.new("R36_REVIEW_SKIN_ONLY")
material.diffuse_color = (0.72, 0.55, 0.45, 1)
body.data.materials.clear()
body.data.materials.append(material)
scene.render.engine = "BLENDER_WORKBENCH"
sh = scene.display.shading
sh.light, sh.color_type, sh.show_cavity = "STUDIO", "MATERIAL", True
scene.render.film_transparent = True
scene.render.resolution_x = scene.render.resolution_y = 512
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
cd = bpy.data.cameras.new("R36_REVIEW_CAMERA")
cd.type, cd.ortho_scale = "ORTHO", 1.15
cam = bpy.data.objects.new("R36_REVIEW_CAMERA", cd)
scene.collection.objects.link(cam)
scene.camera = cam
views = {"back": (0, 1, 0.02), "front": (0, -1, 0.02), "three_quarter": (0.7, 0.7, 0.05)}
if len(args) > 2 and args[2] in ("front_closeups", "junction_closeups"):
    junction = args[2] == "junction_closeups"
    import build_original_sculpt_corrective_blender as sculpt
    scene.render.resolution_x = scene.render.resolution_y = 768
    cd.ortho_scale = 0.30
    for ht in (120., 130., 135.625, 145., 156.):
        bench._reset(rig)
        sculpt.press_pose(res, ht)
        drives.drive(rig, body)
        for side in ('l','r'):
            sign = 1 if side == 'r' else -1
            gh = rig.matrix_world @ rig.pose.bones['upperarm_'+side].head
            target = gh + Vector((sign*0.03, 0.01 if junction else -0.02, -0.03))
            close_views = {'back': views['back'], 'three_quarter': (sign*.7,.7,.05)} if junction else {'front':views['front']}
            for name,direction in close_views.items():
                d = Vector(direction).normalized()
                cd.ortho_scale = 0.42 if junction else 0.30
                cam.location = target + d * 4
                cam.rotation_mode = 'QUATERNION'
                cam.rotation_quaternion = (-d).to_track_quat('-Z','Y')
                scene.render.filepath = str(out / f'{side}_{name}_{ht}.png')
                bpy.ops.render.render(write_still=True)
    print("EXACT_CLOSEUPS", model.name, flush=True)
    raise SystemExit(0)

rows = []
for n in range(41):
    bench._reset(rig)
    state = px.pose_press_full(res, n / 40)
    drives.drive(rig, body)
    for name, direction in views.items():
        d = Vector(direction).normalized()
        target = Vector((0, 0, 1.45))
        cam.location = target + d * 4
        cam.rotation_mode = "QUATERNION"
        cam.rotation_quaternion = (-d).to_track_quat("-Z", "Y")
        scene.render.filepath = str(out / f"f{n:03d}_{name}.png")
        bpy.ops.render.render(write_still=True)
    rows.append({"t": n / 40, **state})
(out / "frames.json").write_text(json.dumps(rows, indent=2) + "\n")
print("RENDERED", model.name, len(rows), flush=True)

