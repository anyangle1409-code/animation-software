"""Render frozen evaluated W8 snapshots in a fresh Blender process, never a source.

Uniform diagnostic material and shared orthographic cameras; no clinical approval.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

W8_SHA = '2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c'
CONDITIONS = ('observed', 'S5_muted', 'S7_muted', 'all_nonbasis_keys_muted')


def camera_plan(vertices, focus_ids):
    if not focus_ids or any(i < 0 or i >= len(vertices) for i in focus_ids):
        raise ValueError('missing focus endpoint')
    points = [tuple(float(v) for v in vertices[i]) for i in focus_ids]
    if any(len(p) != 3 or not all(math.isfinite(v) for v in p) for p in points):
        raise ValueError('focus must be finite 3D points')
    lo = [min(p[i] for p in points) for i in range(3)]
    hi = [max(p[i] for p in points) for i in range(3)]
    center = [(a+b)/2 for a,b in zip(lo, hi)]
    scale = max(0.3, max(b-a for a,b in zip(lo, hi))*1.3 + 0.15)
    return {'focus_world_m': center, 'ortho_scale_m': scale,
            'axis_views': {'axis_negY': [0, -1, 0], 'axis_posY': [0, 1, 0],
                           'axis_posX': [1, 0, 0]},
            'anatomical_view_or_side_certified': False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--snapshots', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--exposure', type=float, default=-0.5)
    parser.add_argument('--light-energy', type=float, default=35.0)
    args = parser.parse_args()
    if (not math.isfinite(args.exposure) or not math.isfinite(args.light_energy)
            or args.light_energy <= 0):
        raise ValueError('positive light energy and finite render settings required')
    import numpy as np
    import bpy
    from mathutils import Vector
    from PIL import Image, ImageDraw
    args.out.mkdir(parents=True, exist_ok=False)
    scene = bpy.data.scenes.new('HGPT_DIAGNOSTIC_SNAPSHOT_SCENE')
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 32
    scene.cycles.use_denoising = False
    scene.cycles.max_bounces = 2
    scene.render.resolution_x = scene.render.resolution_y = 384
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.exposure = args.exposure
    scene.world = bpy.data.worlds.new('diagnostic_world')
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get('Background')
    background.inputs['Color'].default_value = (0.18, 0.18, 0.18, 1)
    background.inputs['Strength'].default_value = 0.35
    camera_data = bpy.data.cameras.new('fixed_orthographic_camera')
    camera = bpy.data.objects.new('fixed_orthographic_camera', camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera_data.type = 'ORTHO'
    material = bpy.data.materials.new('uniform_diagnostic_gray')
    material.diffuse_color = (0.55, 0.60, 0.66, 1)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (0.55, 0.60, 0.66, 1)
    bsdf.inputs['Roughness'].default_value = 0.8
    lights = []
    for i, offset in enumerate(((1, -2, 2), (-1, 2, 1))):
        ld = bpy.data.lights.new('fixed_area_'+str(i), 'AREA')
        ld.energy, ld.size = args.light_energy, 2
        ob = bpy.data.objects.new(ld.name, ld)
        scene.collection.objects.link(ob)
        lights.append((ob, offset))
    manifest = {'status': 'ACTUAL_BLENDER_RENDER_OF_FROZEN_EVALUATED_GEOMETRY_NOT_REPAIR',
                'source_sha256': W8_SHA, 'renderer': 'Blender Cycles CPU, 32 samples, 384 square, AgX',
                'exposure': args.exposure, 'area_light_energy': args.light_energy,
                'original_blend_opened_by_renderer': False, 'saved_blend': False,
                'anatomical_approval': False, 'samples': [],
                'limitations': ['Diagnostic gray material and smooth normals; source geometry unchanged.',
                               'Shared cameras/lights per pose; no view labels certify anatomical sides.',
                               'Only sampled press conditions; no new generic motion, contact or repair approved.']}
    for sample in (0, 6):
        files = {c: args.snapshots / f'sample{sample:02d}__{c}.npz' for c in CONDITIONS}
        with np.load(files['observed'], allow_pickle=False) as observed:
            plan = camera_plan(observed['vertices'], observed['focus_ids'].tolist())
            reference_faces = observed['faces'].copy()
        focus = Vector(plan['focus_world_m'])
        scale = plan['ortho_scale_m']
        camera_data.ortho_scale = scale
        camera_data.clip_start, camera_data.clip_end = 0.01, 100
        for light, offset in lights:
            light.location = focus + Vector(offset)*scale
            light.rotation_euler = (focus-light.location).to_track_quat('-Z', 'Y').to_euler()
        record = {'sample': sample, 'camera_plan': plan, 'conditions': []}
        for condition, file in files.items():
            with np.load(file, allow_pickle=False) as data:
                if str(data['source_sha256']) != W8_SHA:
                    raise ValueError('unverified snapshot source')
                vertices, faces = data['vertices'], data['faces']
                if (vertices.ndim != 2 or vertices.shape[1] != 3 or not np.isfinite(vertices).all()
                        or faces.ndim != 2 or faces.shape[1] != 3 or faces.dtype.kind not in 'iu'
                        or not np.array_equal(faces, reference_faces)
                        or faces.min() < 0 or faces.max() >= len(vertices)):
                    raise ValueError('invalid snapshot geometry or topology')
                mesh = bpy.data.meshes.new('evaluated_snapshot')
                mesh.from_pydata(vertices.tolist(), [], faces.tolist())
                mesh.update()
                mesh.polygons.foreach_set('use_smooth', [True]*len(mesh.polygons))
                mesh.materials.append(material)
                obj = bpy.data.objects.new('evaluated_snapshot', mesh)
                scene.collection.objects.link(obj)
                images = {}
                try:
                    for view, direction in plan['axis_views'].items():
                        camera.location = focus + Vector(direction)*(scale*3)
                        camera.rotation_euler = (focus-camera.location).to_track_quat('-Z', 'Y').to_euler()
                        target = args.out / f'sample{sample:02d}__{condition}__{view}.png'
                        scene.render.filepath = str(target.resolve())
                        bpy.ops.render.render(write_still=True, scene=scene.name)
                        images[view] = {'file': target.name, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest()}
                finally:
                    bpy.data.objects.remove(obj, do_unlink=True)
                    bpy.data.meshes.remove(mesh)
                record['conditions'].append({'condition': condition,
                    'snapshot_npz_sha256': hashlib.sha256(file.read_bytes()).hexdigest(),
                    'vertices_float64_sha256': hashlib.sha256(vertices.astype('<f8').tobytes()).hexdigest(),
                    'images': images})
        for view in plan['axis_views']:
            sheet = Image.new('RGB', (768, 854), '#eef0f4')
            draw = ImageDraw.Draw(sheet)
            draw.text((12, 8), f'W8 sample {sample} / {view} / native diagnostic / NOT APPROVED', fill='black')
            for i, record_condition in enumerate(record['conditions']):
                x, y = (i%2)*384, 38+(i//2)*408
                draw.text((x+8, y), record_condition['condition'], fill='black')
                with Image.open(args.out / record_condition['images'][view]['file']) as im:
                    sheet.paste(im.convert('RGB'), (x, y+20))
            sheet.save(args.out / f'sample{sample:02d}__{view}__comparison.png')
        manifest['samples'].append(record)
    (args.out / 'native_control_view_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print('NATIVE_CONTROL_VIEWS_WRITTEN', 24, 'renders', 6, 'sheets; NO_ANATOMICAL_APPROVAL', flush=True)


if __name__ == '__main__':
    main()
