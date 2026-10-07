#!/usr/bin/env python3
"""Render review images of HGPT_ANATOMICAL_MASTER inside the translucent r95 body (audit evidence only).

Bones are drawn as temporary stick meshes coloured by placement class; joint centres as spheres. Nothing is
saved back to any .blend. Run: python3 render_master_review.py --blend A002 --record FIT.json --out DIR
"""
import argparse, json, math, sys
from pathlib import Path
import bpy
from mathutils import Vector

COLOURS = {'regression': (0.85, 0.15, 0.15, 1), 'surface_landmark': (0.95, 0.6, 0.1, 1),
           'surface_station': (0.2, 0.55, 0.95, 1), 'proportional': (0.55, 0.55, 0.6, 1)}


def material(name, rgba):
    m = bpy.data.materials.new(name)
    m.diffuse_color = rgba
    return m


def stick(name, a, b, r, mat, coll):
    a, b = Vector(a), Vector(b)
    d = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=r, depth=d.length, location=(a + b) / 2)
    o = bpy.context.active_object
    o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    o.name = name
    o.data.materials.append(mat)
    for c in o.users_collection:
        c.objects.unlink(o)
    coll.objects.link(o)


def ball(name, p, r, mat, coll):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=6, radius=r, location=p)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(mat)
    for c in o.users_collection:
        c.objects.unlink(o)
    coll.objects.link(o)


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument('--blend', required=True); ap.add_argument('--record', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--views', default='all')
    o = ap.parse_args(argv)
    bpy.ops.wm.open_mainfile(filepath=str(Path(o.blend).resolve()))
    rec = json.loads(Path(o.record).read_text())
    out = Path(o.out); out.mkdir(parents=True, exist_ok=True)
    sc = bpy.context.scene
    for ob in sc.objects:
        if ob.type == 'MESH' and ob.name != 'HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE':
            ob.hide_render = True
    body = bpy.data.objects['HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE']
    body.data.materials.clear()
    body.data.materials.append(material('skin', (0.85, 0.8, 0.75, 1)))
    coll = bpy.data.collections.new('REVIEW_ONLY'); sc.collection.children.link(coll)
    mats = {k: material(k, c) for k, c in COLOURS.items()}
    jmat = material('joint', (0.1, 0.75, 0.3, 1))
    rigmat = material('runtime', (0.9, 0.1, 0.9, 1))
    for bid, b in rec['bones'].items():
        L = math.dist(b['head_m'], b['tail_m'])
        stick('B_' + bid, b['head_m'], b['tail_m'], max(0.0012, min(0.006, L * 0.03)), mats[b['placement']], coll)
    major = ['hip', 'tibiofemoral', 'talocrural', 'glenohumeral', 'acromioclavicular', 'sternoclavicular', 'humeroulnar', 'radiocarpal', 'subtalar_posterior']
    for jid, m in rec['joint_markers'].items():
        r = 0.007 if any(jid.startswith(k + '_') for k in major) else 0.0025
        ball('J_' + jid, m['centre_m'], r, jmat, coll)
    if o.views in ('all', 'compare'):
        for k, v in rec['checks']['runtime_rig_comparison']['joints'].items():
            ball('R_' + k, v['runtime_head_m'], 0.006, rigmat, coll)
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading
    sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'
    sh.show_xray = True; sh.xray_alpha = 0.25
    sc.render.film_transparent = False
    sc.world = sc.world or bpy.data.worlds.new('w')
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'
    views = {'full_front': ((0, -4, 0.91), (0, 0, 0.91), 1.95, (900, 1500)), 'full_left_lateral': ((4, 0, 0.91), (0, 0, 0.91), 1.95, (900, 1500)),
             'full_back': ((0, 4, 0.91), (0, 0, 0.91), 1.95, (900, 1500)),
             'shoulder_front': ((0.15, -3, 1.42), (0.15, 0, 1.42), 0.42, (900, 900)), 'shoulder_lateral': ((3, 0.02, 1.42), (0.2, 0.02, 1.42), 0.42, (900, 900)),
             'pelvis_front': ((0, -3, 0.97), (0, 0, 0.97), 0.45, (900, 900)), 'pelvis_lateral': ((3, 0, 0.97), (0, 0, 0.97), 0.45, (900, 900)),
             'knee_front': ((0.09, -3, 0.5), (0.09, 0, 0.5), 0.3, (900, 900)), 'knee_lateral': ((3, 0, 0.5), (0.09, 0, 0.5), 0.3, (900, 900)),
             'foot_lateral': ((3, -0.1, 0.07), (0.09, -0.1, 0.07), 0.42, (900, 600)), 'foot_top': ((0.09, -0.1, 3), (0.09, -0.1, 0.0), 0.42, (900, 900)),
             'hand_lateral': ((3, 0.02, 0.86), (0.21, 0.02, 0.86), 0.32, (700, 900)), 'spine_lateral': ((3, 0.02, 1.3), (0, 0.02, 1.3), 0.9, (700, 1100)),
             'head_lateral': ((3, 0, 1.69), (0, 0, 1.69), 0.32, (900, 900)), 'head_front': ((0, -3, 1.69), (0, 0, 1.69), 0.32, (900, 900))}
    for name, (loc, target, size, res) in views.items():
        cam.location = loc
        d = Vector(target) - Vector(loc)
        cam.rotation_euler = d.to_track_quat('-Z', 'Y' if abs(d.z) < 0.9 * d.length else 'Y').to_euler()
        cam.data.ortho_scale = size
        sc.render.resolution_x, sc.render.resolution_y = res
        sc.render.filepath = str(out / f'{name}.png')
        bpy.ops.render.render(write_still=True)
    print('rendered', len(views))


if __name__ == '__main__':
    main()
