#!/usr/bin/env python3
"""Render bone-only movement clips (animated GIF) of selected isolated sweeps on HGPT_ANATOMICAL_MASTER.

Stick meshes are bone-parented to the master so they follow the authored test animation. The character
surface is not skinned to the master and is therefore not shown. Nothing is saved back to any .blend.
Run: python3 render_test_clips.py --blend TESTS.blend --record FIT.json --report RUN/isolated_report.json --out DIR
"""
import argparse, json, math, sys
from pathlib import Path
import bpy
from mathutils import Vector

CLIPS = {  # test id: (camera direction, target bone for framing, ortho size)
    'hip_flexion_extension_left': ('left', 'femur_left', 1.3), 'hip_rotation_at_90_flexion_left': ('top', 'femur_left', 1.2),
    'knee_flexion_extension_left': ('left', 'tibia_left', 1.2), 'talocrural_dorsi_plantarflexion_left': ('left', 'talus_left', 0.45),
    'subtalar_inversion_eversion_left': ('back', 'calcaneus_left', 0.4), 'gh_elevation_plane_0_left': ('front', 'humerus_left', 1.2),
    'gh_elevation_plane_90_left': ('left', 'humerus_left', 1.2), 'gh_axial_rotation_at_90_elevation_left': ('front', 'humerus_left', 1.1),
    'elbow_flexion_at_pronation_60_left': ('left', 'ulna_left', 0.8), 'forearm_rotation_at_elbow_90_left': ('front', 'radius_left', 0.7),
    'wrist_flexion_left': ('front', 'capitate_left', 0.45), 'digit3_flexion_left': ('front', 'digit3_proximal_phalanx_left', 0.3),
    'c1_c2_axial_rotation': ('top', 'c1', 0.5), 'lumbar_l4_l5_extension': ('left', 'l4', 1.4),
    'shoulder_complex_scapular_plane_left': ('front', 'scapula_left', 1.1), 'knee_flexion_with_screw_home_left': ('front', 'tibia_left', 1.0)}
DIRS = {'left': Vector((1, 0, 0)), 'front': Vector((0, -1, 0)), 'back': Vector((0, 1, 0)), 'top': Vector((0, 0, 1))}


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    for a in ('--blend', '--record', '--report', '--out'):
        ap.add_argument(a, required=True)
    ap.add_argument('--step', type=int, default=2)
    ap.add_argument('--only', default='')
    o = ap.parse_args(argv)
    bpy.ops.wm.open_mainfile(filepath=str(Path(o.blend).resolve()))
    rec = json.loads(Path(o.record).read_text())
    rep = json.loads(Path(o.report).read_text())
    out = Path(o.out); out.mkdir(parents=True, exist_ok=True)
    sc = bpy.context.scene
    arm = bpy.data.objects['HGPT_ANATOMICAL_MASTER']
    for ob in sc.objects:
        if ob.type in ('MESH', 'EMPTY'):
            ob.hide_render = True
    coll = bpy.data.collections.new('CLIP_ONLY'); sc.collection.children.link(coll)
    colours = {'regression': (0.85, 0.15, 0.15, 1), 'surface_landmark': (0.95, 0.6, 0.1, 1), 'surface_station': (0.2, 0.55, 0.95, 1), 'proportional': (0.7, 0.7, 0.75, 1)}
    mats = {}
    for k, c in colours.items():
        m = bpy.data.materials.new(k); m.diffuse_color = c; mats[k] = m
    for bid, b in rec['bones'].items():
        a, t = Vector(b['head_m']), Vector(b['tail_m'])
        d = t - a
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=max(0.0015, min(0.008, d.length * 0.035)), depth=d.length, location=(a + t) / 2)
        st = bpy.context.active_object
        st.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
        st.data.materials.append(mats[b['placement']])
        for c in st.users_collection:
            c.objects.unlink(st)
        coll.objects.link(st)
        bpy.context.view_layer.update()
        mw = st.matrix_world.copy()
        st.parent, st.parent_type, st.parent_bone = arm, 'BONE', 'anat_' + bid
        bpy.context.view_layer.update()
        st.matrix_world = mw
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'
    sc.render.resolution_x = sc.render.resolution_y = 480
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'
    from PIL import Image
    made = {}
    for tid, (view, bone, size) in CLIPS.items():
        if o.only and tid not in o.only.split(','):
            continue
        a, b = rep['summary'][tid]['frames']
        bb = rec['bones'][bone]
        target = (Vector(bb['head_m']) + Vector(bb['tail_m'])) / 2
        dirv = DIRS[view]
        cam.location = target + dirv * 3
        cam.rotation_euler = (-dirv).to_track_quat('-Z', 'Y' if view != 'top' else 'Y').to_euler()
        cam.data.ortho_scale = size
        frames = []
        for f in range(a, b + 1, o.step):
            sc.frame_set(f)
            p = out / f'_{tid}_{f:05d}.png'
            sc.render.filepath = str(p)
            bpy.ops.render.render(write_still=True)
            frames.append(Image.open(p).convert('P', palette=Image.ADAPTIVE))
            p.unlink()
        gif = out / f'{tid}.gif'
        frames[0].save(gif, save_all=True, append_images=frames[1:], duration=80, loop=0)
        made[tid] = {'gif': gif.name, 'frames': [a, b], 'step': o.step, 'view': view}
    (out / 'clips_manifest.json').write_text(json.dumps({'source_blend': str(Path(o.blend).name), 'clips': made,
        'note': 'Bone-only: master bones are reference anatomy and are not skinned; colours = placement class.'}, indent=1))
    print('clips', len(made))


if __name__ == '__main__':
    main()
