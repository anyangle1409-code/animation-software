"""New isolated W1 shape/rig pilot. Does NOT open or overwrite legacy Blender assets.

Six controls, original authored envelopes around preserved c004 anchors. The
artist-defined coupling is a diagnostic, not a fitted human trajectory. Source
landmark statistics are guides, no CT/scan mesh is loaded or redistributed.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/anatomy_fit'))
from functional_shoulder_shapes import blade_mesh, clavicle_points

RECORD = 'ORIGINAL_V1_WORK/anatomy/audit/candidates/shoulder_thorax_c004_arm_inputs/candidate_record.json'
VERSION = 'PROVISIONAL_FUNCTIONAL_SHOULDER_v1'


def material(name, colour):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*colour, 1)
    return mat


def tube(name, points, radius, mat):
    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '3D'
    curve.resolution_u = 1
    curve.bevel_depth = radius
    curve.bevel_resolution = 3
    curve.use_fill_caps = True
    spline = curve.splines.new('POLY')
    spline.points.add(len(points) - 1)
    for p, coord in zip(spline.points, points):
        p.co = (*coord, 1)
    ob = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.convert(target='MESH')
    ob = bpy.context.object
    ob.select_set(False)
    ob.data.materials.append(mat)
    return ob


def bind(ob, arm, bone):
    world = ob.matrix_world.copy()
    ob.parent = arm
    ob.matrix_world = world
    group = ob.vertex_groups.new(name=bone)
    group.add(list(range(len(ob.data.vertices))), 1, 'REPLACE')
    mod = ob.modifiers.new('shape_follows_skeleton', 'ARMATURE')
    mod.object = arm
    ob['anatomical_control'] = bone
    ob['status'] = 'AUTHORED_PROVISIONAL_ENVELOPE_NOT_SOURCE_SURFACE'


def build(rec):
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    sc = bpy.context.scene
    sc['candidate'] = VERSION
    sc['anatomy_approved'] = False
    sc['motion_approved'] = False
    sc['production_approved'] = False
    data = bpy.data.armatures.new('functional_shoulder_controls')
    arm = bpy.data.objects.new('functional_shoulder_controls', data)
    sc.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    for side in ('left', 'right'):
        src = rec['bones']
        for part in ('clavicle', 'scapula', 'humerus'):
            name = part + '_' + side
            bone = data.edit_bones.new(name)
            bone.head = src[name]['head_m'] if part != 'scapula' else src['clavicle_' + side]['tail_m']
            bone.tail = src[name]['tail_m']
            if part != 'clavicle':
                bone.parent = data.edit_bones[('clavicle' if part == 'scapula' else 'scapula') + '_' + side]
    bpy.ops.object.mode_set(mode='OBJECT')
    arm.select_set(False)
    mats = {k: material(k, c) for k, c in {
        'clavicle': (.95, .70, .20), 'scapula': (.15, .65, .85),
        'humerus': (.87, .84, .72), 'SC': (1, .25, .10), 'AC': (.98, .98, .98), 'GH': (.85, .12, .5)}.items()}
    shapes = []
    for side in ('left', 'right'):
        src = rec['bones']
        clav = src['clavicle_' + side]
        ob = tube('clavicle_shape_' + side, clavicle_points(clav['head_m'], clav['tail_m']), .006, mats['clavicle'])
        bind(ob, arm, 'clavicle_' + side)
        shapes.append(ob)
        lm = [tuple(v / 1000 for v in p) for p in rec['candidate']['scapula_landmarks_world_mm'][side]]
        # Blade border only. Glenoid/acromion/coracoid are separate guides, not
        # guessed detail blended into a supposedly measured articular surface.
        perimeter = [lm[i - 1] for i in (3, 4, 5, 6, 7, 8, 9, 12, 13, 15, 18, 1, 2)]
        verts, faces = blade_mesh(perimeter)
        mesh = bpy.data.meshes.new('scapula_blade_' + side)
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        ob = bpy.data.objects.new(mesh.name, mesh)
        sc.collection.objects.link(ob)
        ob.data.materials.append(mats['scapula'])
        bind(ob, arm, 'scapula_' + side)
        shapes.append(ob)
        for label, ids, radius in [('spine_acromion', (5, 14, 25, 27, 26), .004),
                                   ('glenoid_rim', (15, 16, 18, 17, 15), .003),
                                   ('coracoid_guide', (20, 22, 23), .004)]:
            ob = tube(label + '_' + side, [lm[i-1] for i in ids], radius, mats['scapula'])
            bind(ob, arm, 'scapula_' + side)
            shapes.append(ob)
        hum = src['humerus_' + side]
        ob = tube('humerus_shape_' + side, [hum['head_m'], hum['tail_m']], .013, mats['humerus'])
        bind(ob, arm, 'humerus_' + side)
        shapes.append(ob)
        for label, centre, owner, radius in [('SC', clav['head_m'], 'clavicle', .008),
                                              ('AC', clav['tail_m'], 'clavicle', .008),
                                              ('GH', hum['head_m'], 'scapula', .024)]:
            bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=radius, location=centre)
            ob = bpy.context.object
            ob.name = label + '_' + side
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            ob.data.materials.append(mats[label])
            bind(ob, arm, owner + '_' + side)
            shapes.append(ob)
            ob.select_set(False)
    return arm, shapes


def around(p, rotation):
    return Matrix.Translation(p) @ rotation @ Matrix.Translation(-p)


def pose(arm, rec, angle):
    if not 0 <= angle <= 160:
        raise ValueError('diagnostic range only 0..160')
    t = angle / 160
    # Authored nonuniform response: direction evidence only; no universal 2:1.
    f = t * t * (3 - 2 * t)
    for side, sign in [('left', 1), ('right', -1)]:
        sc = Vector(rec['bones']['clavicle_' + side]['head_m'])
        ac = Vector(rec['bones']['clavicle_' + side]['tail_m'])
        gh = Vector(rec['bones']['humerus_' + side]['head_m'])
        chord = (ac - sc).normalized()
        rotation = (Matrix.Rotation(math.radians(-sign * 12 * f), 4, 'Y') @
                    Matrix.Rotation(math.radians(sign * 10 * f), 4, 'Z') @
                    Matrix.Rotation(math.radians(sign * 28 * f), 4, chord))
        dc = around(sc, rotation)
        new_ac = dc @ ac
        ds = (around(new_ac, Matrix.Rotation(math.radians(-sign * 52 * f), 4, 'Y') @
                     Matrix.Rotation(math.radians(-16 * f), 4, 'X')) @ dc)
        new_gh = ds @ gh
        dh = Matrix.Translation(new_gh) @ Matrix.Rotation(math.radians(-sign * angle), 4, 'Y') @ Matrix.Translation(-gh)
        for part, delta in [('clavicle', dc), ('scapula', ds), ('humerus', dh)]:
            name = part + '_' + side
            arm.pose.bones[name].matrix = delta @ arm.data.bones[name].matrix_local
            bpy.context.view_layer.update()


def matrices(arm):
    return {b.name: {'rest_world_row_major': [list(r) for r in b.matrix_local],
                     'pose_world_row_major': [list(r) for r in arm.pose.bones[b.name].matrix],
                     'skin_palette_native_row_major': [list(r) for r in arm.pose.bones[b.name].matrix @ b.matrix_local.inverted()]}
            for b in arm.data.bones}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    args = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
    out = Path(args.out).resolve()
    if out.exists():
        raise FileExistsError(out)
    source = ROOT / RECORD
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    rec = json.loads(source.read_text())
    arm, shapes = build(rec)
    out.mkdir(parents=True)
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'STUDIO'
    sc.display.shading.color_type = 'MATERIAL'
    sc.display.shading.show_shadows = True
    sc.display.shading.show_cavity = True
    sc.render.resolution_x, sc.render.resolution_y = 800, 800
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'
    cam = bpy.data.objects.new('review_camera', bpy.data.cameras.new('review_camera'))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = .85
    title = bpy.data.curves.new('candidate_warning', 'FONT')
    title.body = VERSION + '\nSHOULDER GUIDES ONLY / NOT HUMAN OR MOTION APPROVED'
    title.size = .013
    caption = bpy.data.objects.new('candidate_warning', title)
    sc.collection.objects.link(caption)
    caption.parent = cam
    caption.location = (-.40, .38, -1)
    caption.data.materials.append(material('caption', (.95, .95, .95)))
    target = Vector((0, .04, 1.43))
    frame_data = []
    for angle in (0, 45, 90, 135, 160, 90, 0):
        pose(arm, rec, angle)
        frame_data.append({'time_seconds': len(frame_data), 'authored_arm_rotation_from_rest_deg': angle, 'controls': matrices(arm)})
    for angle in (0, 45, 90, 160):
        pose(arm, rec, angle)
        for view, location in [('front', (0, -3, 1.43)), ('side', (3, .04, 1.43)),
                                ('rear', (0, 3, 1.43)), ('three_quarter', (2, -2, 1.8)),
                                ('overhead', (0, .041, 4))]:
            cam.location = location
            cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
            sc.render.filepath = str(out / f'{VERSION}_{angle:03}_{view}.png')
            bpy.ops.render.render(write_still=True)
    pose(arm, rec, 0)
    bpy.ops.wm.save_as_mainfile(filepath=str(out / (VERSION + '.blend')))
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    for ob in shapes:
        ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(out / (VERSION + '.glb')), export_format='GLB',
                              use_selection=True, export_animations=False, export_yup=True)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before
    report = {'candidate': VERSION, 'source_record_sha256': before, 'source_record': RECORD,
              'status': 'PROVISIONAL_SHOULDER_ONLY_NOT_ORIGINAL_HUMAN',
              'anatomy_approved': False, 'motion_approved': False, 'production_approved': False,
              'native_frame': '+X anatomical left / +Y posterior / +Z superior; metres',
              'glb_frame': 'Blender exporter Y-up conversion; actual GLB joint-order/bind preflight PENDING',
              'rig_mapping': {b.name: {'anatomical_id': b.name, 'parent': b.parent.name if b.parent else None} for b in arm.data.bones},
              'frames': frame_data, 'blender': bpy.app.version_string,
              'files_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()},
              'known_defects': ['No human skin or muscle mesh yet', 'c004 neutral anchors remain provisional',
                                'Authored curve radii, thickness and movement trajectory NOT measured',
                                'Scapula fan is a coarse guide; not an anatomical articular surface',
                                'Human photo/video, loaded movement and thorax-contact validation pending']}
    (out / 'pilot_manifest.json').write_text(json.dumps(report, indent=2))
    print('PILOT_REPORT', json.dumps({k: v for k, v in report.items() if k not in ('frames', 'files_sha256')}))


if __name__ == '__main__':
    main()
