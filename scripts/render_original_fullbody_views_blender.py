#!/usr/bin/env python3
"""Full-body phone review renders of an ORIGINAL_v1 body (bpy, Workbench, orthographic, rest pose by default).

Views: front, rear, side_right (+X), side_left (-X), three_quarter_front, three_quarter_rear.  Every view uses the same
ortho scale, a floor line and a 0.5 m scale bar, so renders of different candidates are directly comparable.  Only the
named body is drawn; nothing is saved to the blend.

  python3.13 render_original_fullbody_views_blender.py --blend B.blend --out DIR [--body NAME] [--res 900x1600]
"""
import argparse, math, sys
from pathlib import Path

import bpy
from mathutils import Vector

VIEWS = {  # name: camera direction from the body centre (HGPT: -Y is anterior, +X is the runtime _r side)
    'front': (0, -1, 0), 'rear': (0, 1, 0), 'side_plusX': (1, 0, 0), 'side_minusX': (-1, 0, 0),
    'three_quarter_front': (0.7, -0.7, 0.12), 'three_quarter_rear': (-0.7, 0.7, 0.12),
}


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument('--blend', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--body', default='HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE')
    ap.add_argument('--res', default='900x1600')
    o = ap.parse_args(argv)
    bpy.ops.wm.open_mainfile(filepath=str(Path(o.blend).resolve()))
    scene = bpy.context.scene
    body = bpy.data.objects[o.body]
    if body.data.shape_keys:
        for kb in body.data.shape_keys.key_blocks[1:]:
            kb.value = 0.0
    for ob in scene.objects:
        if ob.type in ('MESH', 'CURVE', 'SURFACE', 'META', 'FONT') and ob is not body:
            ob.hide_render = True
    mat = bpy.data.materials.new('HGPT_FB_SKIN_TMP'); mat.diffuse_color = (0.64, 0.46, 0.38, 1.0)
    body.data.materials.clear(); body.data.materials.append(mat)
    grey = bpy.data.materials.new('HGPT_FB_GUIDE_TMP'); grey.diffuse_color = (0.35, 0.35, 0.35, 1.0)
    # floor line and 0.5 m scale bar (thin boxes)
    def box(name, loc, size):
        me = bpy.data.meshes.new(name); ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob)
        import bmesh
        bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(me); bm.free()
        ob.location = loc; ob.scale = size; me.materials.append(grey)
        return ob
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    zs = [(ev.matrix_world @ v.co).z for v in ev.data.vertices]
    zmin, zmax = min(zs), max(zs)
    box('HGPT_FB_FLOOR_TMP', (0, 0, zmin - 0.002), (1.2, 1.2, 0.002))
    box('HGPT_FB_BAR_TMP', (-0.42, 0.42, zmin + 0.25), (0.012, 0.012, 0.5))   # off-axis: visible in every view
    scene.render.engine = 'BLENDER_WORKBENCH'
    sh = scene.display.shading
    sh.light, sh.color_type, sh.show_cavity = 'STUDIO', 'MATERIAL', True
    sh.show_shadows = False
    w, h = (int(x) for x in o.res.split('x'))
    scene.render.resolution_x, scene.render.resolution_y = w, h
    scene.render.image_settings.file_format = 'PNG'
    cd = bpy.data.cameras.new('HGPT_FB_CAM_TMP'); cd.type = 'ORTHO'; cd.ortho_scale = (zmax - zmin) * 1.12 * max(1.0, w / h)
    cam = bpy.data.objects.new('HGPT_FB_CAM_TMP', cd); scene.collection.objects.link(cam); scene.camera = cam
    centre = Vector((0.0, 0.0, 0.5 * (zmin + zmax)))
    out = Path(o.out); out.mkdir(parents=True, exist_ok=True)
    for name, d in VIEWS.items():
        cam.location = centre + Vector(d).normalized() * 5.0
        cam.rotation_euler = (centre - cam.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = str(out / f'{name}.png')
        bpy.ops.render.render(write_still=True)
    print('rendered', len(VIEWS), 'views to', out)


if __name__ == '__main__':
    main()
