#!/usr/bin/env python3
"""Orthographic foot review renders of an ORIGINAL_v1 body (bpy; Workbench). Neutral rest pose, both feet (the +X body side is the native suffix _r foot), matching cameras
for before/after comparison, a 10 mm floor grid and a 50 mm scale bar in every view. Nothing is saved to the blend.

  python3.13 render_original_foot_views_blender.py --blend B.blend --body OBJECT --out DIR [--label TEXT]
"""
import argparse, json, math, sys
from pathlib import Path

import bpy
from mathutils import Vector

VIEWS = {  # name: (camera direction from target, foot set, ortho scale [m], camera distance [m], clip end [m])
    # the camera is placed close to the foot with a clipped frustum so that only the foot region is drawn
    'side_lateral_plusX_foot': ((1, 0, 0), 'plusX', 0.36, 0.30, 0.42),
    'side_medial_plusX_foot': ((-1, 0, 0), 'plusX', 0.36, 0.095, 0.30),
    'top_both': ((0, 0, 1), 'both', 0.46, 0.22, 0.40),
    'sole_both': ((0, 0, -1), 'both', 0.46, 0.12, 0.27),
    'front_both': ((0, -1, 0), 'both', 0.40, 0.45, 0.62),
    'three_quarter_plusX_foot': ((0.62, -0.62, 0.48), 'plusX', 0.40, 0.55, 1.2),
}


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    for a in ('--blend', '--body', '--out'):
        ap.add_argument(a, required=True)
    ap.add_argument('--label', default='')
    o = ap.parse_args(argv)
    bpy.ops.wm.open_mainfile(filepath=str(Path(o.blend).resolve()))
    sc = bpy.context.scene
    body = bpy.data.objects[o.body]
    for ob in sc.objects:
        ob.hide_render = ob is not body
    M = body.matrix_world
    V = [M @ v.co for v in body.data.vertices]
    zmin = min(v.z for v in V)
    foot = [v for v in V if v.z < zmin + 0.16]
    centres = {'plusX': [v for v in foot if v.x > 0.02], 'both': foot}
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'
    sc.display.shading.single_color = (0.80, 0.66, 0.56)
    sc.display.shading.show_cavity = True
    sc.render.resolution_x = 1200; sc.render.resolution_y = 1200
    sc.world = sc.world or bpy.data.worlds.new('w'); sc.world.color = (0.96, 0.96, 0.95)
    # floor grid (10 mm) and a 50 mm scale bar, as thin meshes
    mat = bpy.data.materials.new('grid'); mat.diffuse_color = (0.35, 0.35, 0.40, 1)
    import bmesh
    me = bpy.data.meshes.new('grid'); bm = bmesh.new()
    for i in range(-30, 31):
        for (a, b) in (((i * 0.01, -0.35, zmin - 0.0004), (i * 0.01, 0.10, zmin - 0.0004)),):
            v1, v2 = bm.verts.new(a), bm.verts.new(b); bm.edges.new((v1, v2))
    for j in range(-35, 11):
        v1, v2 = bm.verts.new((-0.30, j * 0.01, zmin - 0.0004)), bm.verts.new((0.30, j * 0.01, zmin - 0.0004)); bm.edges.new((v1, v2))
    bm.to_mesh(me); grid = bpy.data.objects.new('grid', me); sc.collection.objects.link(grid)
    mod = grid.modifiers.new('w', 'WIREFRAME'); mod.thickness = 0.0006; grid.data.materials.append(mat)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0.0, 0.07, zmin + 0.003)); bar = bpy.context.active_object
    bar.scale = (0.05, 0.004, 0.004); bar.location.x = 0.025 + 0.0; bar.data.materials.append(mat)
    cam_d = bpy.data.cameras.new('cam'); cam_d.type = 'ORTHO'; cam = bpy.data.objects.new('cam', cam_d)
    sc.collection.objects.link(cam); sc.camera = cam
    out = Path(o.out); out.mkdir(parents=True, exist_ok=True)
    meta = {}
    for name, (d, which, scale, dist, clip) in VIEWS.items():
        P = centres[which]
        c = Vector(((min(v.x for v in P) + max(v.x for v in P)) / 2, (min(v.y for v in P) + max(v.y for v in P)) / 2, zmin + 0.045))
        dv = Vector(d).normalized()
        cam_d.ortho_scale = scale
        if name == 'side_medial_plusX_foot':
            c2 = Vector((0.0, c.y, c.z)); cam.location = c2 + Vector((0.0005, 0, 0))     # camera on the midline, looking at the +X foot
            dv = Vector((-1, 0, 0))
        else:
            cam.location = c + dv * dist
        cam.rotation_mode = 'QUATERNION'; cam.rotation_quaternion = (-dv).to_track_quat('-Z', 'Y')
        cam_d.clip_start = 0.001; cam_d.clip_end = clip
        p = out / f'{name}.png'; sc.render.filepath = str(p)
        bpy.ops.render.render(write_still=True)
        meta[name] = {'ortho_scale_m': scale, 'target_m': [round(x, 4) for x in c], 'direction': d, 'camera_m': [round(x, 4) for x in cam.location],
                      'clip_end_m': clip}
    (out / 'views.json').write_text(json.dumps({'blend': Path(o.blend).name, 'body': o.body, 'label': o.label, 'floor_z_m': zmin,
                                                'grid_mm': 10, 'scale_bar_mm': 50, 'views': meta}, indent=1) + '\n')
    print('rendered', len(meta))


if __name__ == '__main__':
    main()
