#!/usr/bin/env python3
"""Skeleton-only review renders (bpy; Blender Workbench). Opens a skeleton-only rehearsal blend (no body mesh), adds
temporary stick meshes BONE-parented to every armature bone (so they follow poses) and spheres at joint markers, and renders
orthographic whole-body, regional and movement-extreme views. Nothing is saved; the source blend is hash-checked unchanged.

  python3.13 render_skeleton_only_review.py --blend B.blend --record R.json --out DIR [--movement-blend M.blend --samples S.json]
"""
import argparse, hashlib, json, math, sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

ARM = 'HGPT_ANATOMICAL_MASTER'
REGION_COLOURS = [  # first matching prefix wins
    (('skull', 'frontal', 'parietal', 'occipital', 'temporal', 'sphenoid', 'ethmoid', 'maxilla', 'mandible', 'zygomatic', 'nasal',
      'lacrimal', 'palatine', 'vomer', 'inferior_nasal', 'malleus', 'incus', 'stapes', 'hyoid'), (0.85, 0.75, 0.55, 1)),
    (('c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7', 't1', 't2', 't3', 't4', 't5', 't6', 't7', 't8', 't9', 't10', 't11', 't12',
      'l1', 'l2', 'l3', 'l4', 'l5', 'sacrum', 'coccyx'), (0.9, 0.35, 0.2, 1)),
    (('rib', 'sternum'), (0.95, 0.65, 0.3, 1)),
    (('clavicle', 'scapula'), (0.2, 0.6, 0.9, 1)),
    (('humerus', 'radius', 'ulna'), (0.3, 0.45, 0.85, 1)),
    (('scaphoid', 'lunate', 'triquetrum', 'pisiform', 'trapezium', 'trapezoid', 'capitate', 'hamate', 'metacarpal', 'digit', 'thumb'), (0.55, 0.3, 0.85, 1)),
    (('hip_bone',), (0.2, 0.7, 0.4, 1)),
    (('femur', 'patella', 'tibia', 'fibula'), (0.25, 0.65, 0.65, 1)),
    (('talus', 'calcaneus', 'navicular', 'cuboid', 'medial_cuneiform', 'intermediate_cuneiform', 'lateral_cuneiform', 'metatarsal', 'hallux', 'toe'), (0.6, 0.6, 0.2, 1)),
]
VIEWS = {  # name: (direction from target to camera, up, target, ortho_scale)
    'body_front': ((0, -1, 0), (0, 0, 1), None, 2.05), 'body_back': ((0, 1, 0), (0, 0, 1), None, 2.05),
    'body_left': ((1, 0, 0), (0, 0, 1), None, 2.05), 'body_right': ((-1, 0, 0), (0, 0, 1), None, 2.05),
    'body_front_left_34': ((0.7071, -0.7071, 0), (0, 0, 1), None, 2.05), 'body_back_right_34': ((-0.7071, 0.7071, 0), (0, 0, 1), None, 2.05),
    'shoulders_front': ((0, -1, 0), (0, 0, 1), 'shoulders', 0.62), 'shoulders_top': ((0, 0, 1), (0, -1, 0), 'shoulders', 0.62),
    'spine_left': ((1, 0, 0), (0, 0, 1), 'spine', 1.0), 'spine_back': ((0, 1, 0), (0, 0, 1), 'spine', 1.0),
    'pelvis_front': ((0, -1, 0), (0, 0, 1), 'pelvis', 0.45), 'pelvis_top': ((0, 0, 1), (0, -1, 0), 'pelvis', 0.45),
    'hand_left_palmar': ((-1, 0, 0), (0, 0, 1), 'hand_left', 0.26), 'hand_left_dorsal': ((1, 0, 0), (0, 0, 1), 'hand_left', 0.26),
    'hand_left_radial': ((0, -1, 0), (0, 0, 1), 'hand_left', 0.26), 'hand_right_palmar': ((1, 0, 0), (0, 0, 1), 'hand_right', 0.26),
    'foot_left_medial': ((-1, 0, 0), (0, 0, 1), 'foot_left', 0.34), 'foot_left_top': ((0, 0, 1), (0, -1, 0), 'foot_left', 0.34),
    'foot_left_plantar': ((0, 0, -1), (0, -1, 0), 'foot_left', 0.34), 'head_neck_left': ((1, 0, 0), (0, 0, 1), 'head', 0.4),
}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def colour(bone):
    for prefixes, c in REGION_COLOURS:
        if bone.startswith(prefixes):
            return c
    return (0.6, 0.6, 0.6, 1)


def mat(name, rgba):
    m = bpy.data.materials.new(name); m.diffuse_color = rgba
    return m


def build_overlay(rec, coll):
    arm = bpy.data.objects[ARM]
    mats = {}
    for bid, b in rec['bones'].items():
        a, t = Vector(b['head_m']), Vector(b['tail_m']); d = t - a; L = d.length
        r = max(0.0024, min(0.0065, L * 0.06))                 # display radius only (legibility), not anatomy
        bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=r, depth=L, location=(a + t) / 2)
        o = bpy.context.active_object; o.name = 'STICK_' + bid
        o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
        c = colour(bid); key = str(c)
        mats.setdefault(key, mat('m' + key, c)); o.data.materials.append(mats[key])
        for cc in list(o.users_collection):
            cc.objects.unlink(o)
        coll.objects.link(o)
        bpy.context.view_layer.update()
        mw = o.matrix_world.copy()
        o.parent = arm; o.parent_type = 'BONE'; o.parent_bone = 'anat_' + bid
        bpy.context.view_layer.update()
        o.matrix_world = mw
    jm = mat('joint', (0.1, 0.1, 0.1, 1))
    for jid, m in rec['joint_markers'].items():
        bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=5, radius=0.0028, location=m['centre_m'])
        o = bpy.context.active_object; o.name = 'JOINT_' + jid; o.data.materials.append(jm)
        for cc in list(o.users_collection):
            cc.objects.unlink(o)
        coll.objects.link(o)
        host = m.get('frame_bone')
        if host and 'anat_' + host in arm.data.bones:
            bpy.context.view_layer.update(); mw = o.matrix_world.copy()
            o.parent = arm; o.parent_type = 'BONE'; o.parent_bone = 'anat_' + host
            bpy.context.view_layer.update(); o.matrix_world = mw


def targets(rec):
    B = rec['bones']; J = rec['joint_markers']
    mid = lambda names: sum(((Vector(B[n]['head_m']) + Vector(B[n]['tail_m'])) / 2 for n in names), Vector((0, 0, 0))) / len(names)
    hand = lambda s: mid([n for n in B if n.endswith('_' + s) and n.startswith(('metacarpal', 'capitate', 'digit3'))])
    return {None: Vector((0, 0, 0.91)), 'shoulders': (Vector(J['glenohumeral_left']['centre_m']) + Vector(J['glenohumeral_right']['centre_m'])) / 2,
            'spine': mid(['t8', 'l1', 't1']), 'pelvis': mid(['hip_bone_left', 'hip_bone_right', 'sacrum']),
            'hand_left': hand('left'), 'hand_right': hand('right'),
            'foot_left': mid(['talus_left', 'calcaneus_left', 'metatarsal_2_left']), 'head': mid(['mandible', 'c2', 'frontal'])}


def setup_scene(sc):
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_cavity = False
    sc.render.resolution_x = sc.render.resolution_y = 1100
    sc.render.image_settings.file_format = 'PNG'
    sc.world = sc.world or bpy.data.worlds.new('w'); sc.world.color = (1, 1, 1)
    sh.background_type = 'VIEWPORT'; sh.background_color = (1, 1, 1)
    cam = bpy.data.objects.new('REVIEW_CAM', bpy.data.cameras.new('REVIEW_CAM')); sc.collection.objects.link(cam)
    cam.data.type = 'ORTHO'; cam.data.clip_end = 100; sc.camera = cam
    return cam


def shoot(sc, cam, direction, up, target, scale, path):
    d = Vector(direction).normalized()
    regional = scale < 1.5                     # regional views: near clip box so other body parts cannot occlude the region
    dist = scale * 0.75 if regional else 10.0
    cam.data.clip_start = 0.001; cam.data.clip_end = dist + (scale * 0.75 if regional else 10.0)
    cam.location = target + d * dist
    z = d; x = Vector(up).cross(z).normalized(); y = z.cross(x)
    loc = target + d * dist
    cam.matrix_world = Matrix(((x[0], y[0], z[0], loc[0]), (x[1], y[1], z[1], loc[1]),
                               (x[2], y[2], z[2], loc[2]), (0, 0, 0, 1)))
    cam.data.ortho_scale = scale
    sc.render.filepath = str(path); bpy.ops.render.render(write_still=True)


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    for a in ('--blend', '--record', '--out'):
        ap.add_argument(a, required=True)
    ap.add_argument('--movement-blend'); ap.add_argument('--samples'); ap.add_argument('--tests', default='')
    o = ap.parse_args(argv)
    out = Path(o.out); out.mkdir(parents=True, exist_ok=False)
    rec = json.loads(Path(o.record).read_text()); T = targets(rec)
    manifest = {'source_blend_sha256': sha(o.blend), 'record_sha256': sha(o.record), 'blender': bpy.app.version_string, 'views': {}, 'poses': {}}
    bpy.ops.wm.open_mainfile(filepath=str(Path(o.blend).resolve()))
    sc = bpy.context.scene
    for ob in sc.objects:
        if ob.type == 'MESH':
            ob.hide_render = True                         # skeleton-only: no other meshes
    coll = bpy.data.collections.new('REVIEW_ONLY'); sc.collection.children.link(coll)
    build_overlay(rec, coll); cam = setup_scene(sc)
    for name, (d, up, tgt, s) in VIEWS.items():
        p = out / f'{name}.png'; shoot(sc, cam, d, up, T[tgt], s, p)
        manifest['views'][name] = {'direction': d, 'target': tgt or 'body', 'ortho_scale_m': s}
    if o.movement_blend and o.samples:
        samples = json.loads(Path(o.samples).read_text())
        bpy.ops.wm.open_mainfile(filepath=str(Path(o.movement_blend).resolve()))
        sc = bpy.context.scene
        for ob in sc.objects:
            if ob.type == 'MESH':
                ob.hide_render = True
        coll = bpy.data.collections.new('REVIEW_ONLY'); sc.collection.children.link(coll)
        sc.frame_set(1); build_overlay(rec, coll); cam = setup_scene(sc)
        POSE_VIEW = {'digit': ('hand_left', (0, -1, 0), 0.34), 'hand': ('hand_left', (-1, 0, 0), 0.32), 'wrist': ('hand_left', (0, -1, 0), 0.34), 'thumb': ('hand_left', (0, -1, 0), 0.3),
                     'hip': (None, (0, -1, 0), 2.05), 'knee': (None, (1, 0, 0), 2.05), 'shoulder': ('shoulders', (0, -1, 0), 1.0),
                     'elbow': ('shoulders', (1, 0, 0), 1.2), 'subtalar': ('foot_left', (0, 1, 0), 0.4)}
        for tid in [t for t in o.tests.split(',') if t]:
            fr = max(samples[tid], key=lambda f: sum(abs(v) for k, v in f['commanded'].items() if k != 'glide'))
            key = next(k for k in POSE_VIEW if tid.startswith(k) or k in tid)
            tgt, d, s = POSE_VIEW[key]
            sc.frame_set(fr['frame']); bpy.context.view_layer.update()
            p = out / f'pose_{tid}_f{fr["frame"]}.png'; shoot(sc, cam, d, (0, 0, 1), T[tgt], s, p)
            manifest['poses'][tid] = {'frame': fr['frame'], 'commanded': fr['commanded'], 'view_direction': d}
    manifest['source_blend_sha256_after'] = sha(o.blend)
    manifest['files_sha256'] = {f.name: sha(f) for f in sorted(out.glob('*.png'))}
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1) + '\n')
    print('views', len(manifest['views']), 'poses', len(manifest['poses']), 'unchanged', manifest['source_blend_sha256'] == manifest['source_blend_sha256_after'])


if __name__ == '__main__':
    main()
