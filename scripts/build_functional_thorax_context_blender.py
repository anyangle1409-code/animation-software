"""Separate source-aware shoulder/thorax placement scene. No anatomical acceptance."""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_functional_shoulder_pilot_blender as shoulder
from functional_thorax_shapes import rib_points
from functional_shoulder_shapes import blade_mesh

VERSION = 'PROVISIONAL_THORAX_CONTEXT_v1'

def add_context(rec):
    expected = {f'rib_{n:02}_{side}' for n in range(1, 13) for side in ('left','right')}
    actual = {name for name in rec['bones'] if name.startswith('rib_')}
    if actual != expected:
        raise ValueError('exact bilateral01–12 rib inventory required before construction')
    material = shoulder.material('authored_thorax_context', (.65, .78, .52))
    objects = []
    for name, bone in rec['bones'].items():
        if not name.startswith('rib_'):
            continue
        _, number, side = name.split('_')
        n = int(number)
        # Artist-defined visual bow; not specimen curvature or stature regression.
        bow = .09 + .06 * max(0, 1 - abs(n - 7) / 6)
        ob = shoulder.tube(name + '_authored_context', rib_points(bone['head_m'], bone['tail_m'], side, bow), .004, material)
        objects.append(ob)
    head = Vector(rec['bones']['sternum']['head_m'])
    tail = Vector(rec['bones']['sternum']['tail_m'])
    perimeter = [head + Vector((-.025,0,0)), head + Vector((.025,0,0)),
                 tail + Vector((.012,0,0)), tail + Vector((-.012,0,0))]
    vertices, faces = blade_mesh([tuple(p) for p in perimeter])
    mesh = bpy.data.meshes.new('sternum_authored_plate')
    mesh.from_pydata(vertices, [], faces)
    ob = bpy.data.objects.new('sternum_authored_plate', mesh)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(material)
    objects.append(ob)
    for ob in objects:
        ob['anatomy_approved'] = False
        ob['status'] = 'STATIC_AUTHORED_CONTEXT_NOT_CONTACT_SURFACE'
    return objects

def main(pose_fn=None, version=VERSION, angles=(0, 160), motion_note='AUTHORED STATIC RIB/STERNUM GUIDES / NO CONTACT OR MOTION APPROVAL', build_fn=None, shape_notes=()):
    pose_fn = pose_fn or shoulder.pose
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    out = Path(args.out).resolve()
    if out.exists():
        raise FileExistsError(out)
    source = shoulder.ROOT / shoulder.RECORD
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    rec = json.loads(source.read_text())
    arm, shapes = (build_fn or shoulder.build)(rec)
    context = add_context(rec)
    out.mkdir(parents=True)
    scene = bpy.context.scene
    scene['candidate'] = version
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.color_type = 'MATERIAL'
    scene.display.shading.show_cavity = True
    scene.render.resolution_x = scene.render.resolution_y = 800
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    cam = bpy.data.objects.new('review_camera', bpy.data.cameras.new('review_camera'))
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam.data.type = 'ORTHO'
    title = bpy.data.curves.new('provisional_warning', 'FONT')
    title.body = version + '\n' + motion_note
    caption = bpy.data.objects.new('provisional_warning', title)
    scene.collection.objects.link(caption)
    caption.parent = cam
    title.materials.append(shoulder.material('warning', (.95,.95,.95)))
    target = Vector((0, .02, 1.40))
    samples = []
    for angle in angles:
        pose_fn(arm, rec, angle)
        samples.append({'requested_angle': angle, 'native_control_matrices': shoulder.matrices(arm),
                        'measured_HT_elevation_deg': {side: math.degrees(math.acos(max(-1, min(1, -(arm.pose.bones['humerus_' + side].tail - arm.pose.bones['humerus_' + side].head).normalized().z)))) for side in ('left','right')}})
        for view, location in [('front',(0,-3,1.4)),('side',(3,.02,1.4)),('rear',(0,3,1.4))]:
            cam.location = location
            cam.rotation_euler = (target - cam.location).to_track_quat('-Z','Y').to_euler()
            shoulder.fit_review_camera(cam, shapes + context)
            caption.location = (-.47 * cam.data.ortho_scale, .45 * cam.data.ortho_scale, -1)
            title.size = .012 * cam.data.ortho_scale
            scene.render.filepath = str(out / f'{version}_{angle:03}_{view}.png')
            bpy.ops.render.render(write_still=True)
    pose_fn(arm, rec, 0)
    bpy.ops.wm.save_as_mainfile(filepath=str(out / (version + '.blend')))
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before
    report = {'candidate': version, 'motion_note': motion_note, 'samples': samples, 'source_record_sha256': before, 'static_context_meshes': len(context),
              'approval': False, 'contact_validated': False, 'human_reference_compared': False,
              'assumptions': ['Rib lateral bows9-15cm and tube radius4mm authored, not measured',
                              'Sternum plate half-width25/12mm and inherited4mm fan thickness authored',
                              'Inherited sternum endpoints/length/pitch and low-confidence rib endpoints unchanged',
                              'Static thorax; no breathing, cartilage, scapulothoracic mechanics or full-body rig',
                              'Blade and rib tube guides are not approved collision/contact surfaces'] + list(shape_notes),
              'files_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()}}
    (out / 'thorax_context_manifest.json').write_text(json.dumps(report, indent=2))
    print('THORAX_CONTEXT', json.dumps(report))

if __name__ == '__main__':
    main()
