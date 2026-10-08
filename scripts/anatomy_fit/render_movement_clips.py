#!/usr/bin/env python3
"""Render frames of keyed Phase 9 isolated tests from a test .blend (bpy). Read-only: never saves.

Bone sticks are parented to their armature bones so the solver's keyed motion (including follower couplings such as
the scapulothoracic rhythm and clavicle followers) is what moves them. Shoulder bones cyan; SC/AC/GH balls parented to
clavicle/clavicle/scapula; scapula outline points parented to the scapula. The body mesh is not skinned to the
anatomical master and is shown only for scale (static, faint).

  python3.13 render_movement_clips.py --blend TEST.blend --record FIT.json --report isolated_report.json \
      --tests t1,t2 --views front,rear --step 4 --out DIR
"""
import argparse, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
from render_master_review import COLOURS, ball, material, stick  # noqa: E402
from render_shoulder_candidate_review import BODY, SHOULDER_BONES, outline_points  # noqa: E402

CAMS = {'front': Vector((0, -1, 0)), 'rear': Vector((0, 1, 0)), 'left': Vector((1, 0, 0)), 'right': Vector((-1, 0, 0))}


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    for a in ('--blend', '--record', '--report', '--tests', '--views', '--out'):
        ap.add_argument(a, required=True)
    ap.add_argument('--step', type=int, default=4)
    o = ap.parse_args(argv)
    out = Path(o.out); out.mkdir(parents=True, exist_ok=False)
    rec = json.loads(Path(o.record).read_text()); rep = json.loads(Path(o.report).read_text())
    bpy.ops.wm.open_mainfile(filepath=str(Path(o.blend).resolve()))
    sc = bpy.context.scene
    arm = bpy.data.objects['HGPT_ANATOMICAL_MASTER']
    for ob in sc.objects:
        if ob.type in ('MESH', 'EMPTY') and ob.name != BODY:
            ob.hide_render = True
    body = bpy.data.objects[BODY]
    body.data.materials.clear(); body.data.materials.append(material('skin', (0.82, 0.78, 0.74, 1)))
    coll = bpy.data.collections.new('REVIEW_ONLY'); sc.collection.children.link(coll)
    mats = {k: material(k, c) for k, c in COLOURS.items()}
    hi = material('shoulder_hi', (0.1, 0.85, 0.95, 1))
    jm = {'SC': material('SC', (1.0, 0.85, 0.1, 1)), 'AC': material('AC', (0.95, 0.95, 0.95, 1)), 'GH': material('GH', (0.9, 0.15, 0.85, 1))}
    sc.frame_set(1)                                         # rest frame: every test keys rest at both ends
    bpy.context.view_layer.update()

    def attach(ob, bone):
        bpy.context.view_layer.update()                     # stick rotation is set after creation: refresh first
        mw = ob.matrix_world.copy()
        ob.parent, ob.parent_type, ob.parent_bone = arm, 'BONE', 'anat_' + bone
        bpy.context.view_layer.update()
        ob.matrix_world = mw
    for bid, b in rec['bones'].items():
        L = (Vector(b['tail_m']) - Vector(b['head_m'])).length
        sh = bid in SHOULDER_BONES
        stick('B_' + bid, b['head_m'], b['tail_m'], 0.006 if sh else max(0.0012, min(0.006, L * 0.03)),
              hi if sh else mats.get(b['placement'], mats['proportional']), coll)
        attach(bpy.data.objects['B_' + bid], bid)
    for side in ('left', 'right'):
        for key, jid, bone in (('SC', 'sternoclavicular', 'clavicle'), ('AC', 'acromioclavicular', 'clavicle'), ('GH', 'glenohumeral', 'scapula')):
            ball(f'J_{key}_{side}', rec['joint_markers'][f'{jid}_{side}']['centre_m'], 0.011, jm[key], coll)
            attach(bpy.data.objects[f'J_{key}_{side}'], f'{bone}_{side}')
    for side, parts in outline_points(rec).items():
        for name in ('triangle', 'spine', 'glenoid'):
            pts = parts[name]
            for i in range(len(pts) - 1):
                stick(f'O_{side}_{name}_{i}', pts[i], pts[i + 1], 0.0025, hi, coll)
                attach(bpy.data.objects[f'O_{side}_{name}_{i}'], f'scapula_{side}')
    sc.render.engine = 'BLENDER_WORKBENCH'
    shd = sc.display.shading; shd.light = 'STUDIO'; shd.color_type = 'MATERIAL'; shd.show_xray = True; shd.xray_alpha = 0.12
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 1.3
    sc.render.resolution_x = sc.render.resolution_y = 640
    sc.render.image_settings.file_format = 'PNG'
    manifest = {}
    for tid in o.tests.split(','):
        f0, f1 = rep['summary'][tid]['frames']
        frames = list(range(f0, f1 + 1, o.step))
        if frames[-1] != f1:
            frames.append(f1)
        for view in o.views.split(','):
            centre = Vector((0, 0, 1.30)); d = CAMS[view]
            cam.location = centre + d * 3
            cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
            for f in frames:
                sc.frame_set(f)
                sc.render.filepath = str(out / tid / view / f'f{f:05d}.png')
                bpy.ops.render.render(write_still=True)
            manifest[f'{tid}/{view}'] = {'frames': frames}
    (out / 'clips_manifest.json').write_text(json.dumps({'blend': o.blend, 'record': o.record, 'tests': manifest}, indent=1) + '\n')
    print('clips', len(manifest))


if __name__ == '__main__':
    main()
