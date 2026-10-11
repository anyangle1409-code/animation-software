"""Private Blender views along SOURCE axes, not accepted anatomical views.

All raw triangles, including degenerate faces, are retained for display.
No welding, island deletion, smoothing, scaling, registration or blend save.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from source_surface_component_geometry import MAX_BYTES, analyze, require_private


def review(source, expected_sha256, output, resolution=512):
    src, out = require_private(Path(source)), require_private(Path(output))
    if Path(source).is_symlink() or Path(output).is_symlink() or out.exists():
        raise ValueError('Symlinks and existing review directories refused')
    if src.stat().st_size > MAX_BYTES:
        raise ValueError('Oversized source')
    raw = src.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha256:
        raise ValueError('Source digest mismatch')
    diagnostic = analyze(raw)
    if not 32 <= resolution <= 2048:
        raise ValueError('Review resolution outside bounded range')
    vertices = []
    for i in range(diagnostic['raw_faces']):
        values = struct.unpack_from('<9f', raw, 96+50*i)
        vertices.extend(tuple(values[j:j+3]) for j in (0,3,6))
    # Bound the diagnostic camera, not the source geometry. Python doubles
    # check this before conversion to Blender's float32 vectors or any output.
    lo=[min(p[j] for p in vertices) for j in range(3)]
    hi=[max(p[j] for p in vertices) for j in range(3)]
    span=max(hi[j]-lo[j] for j in range(3))
    if not 1e-4 <= span <= 1e6 or max(abs(x) for x in lo+hi)/span > 1e5:
        raise ValueError('Unsupported source extent/offset for an unscaled diagnostic camera')
    # Diagnostic scene only; factory-startup or existing user scene is NOT saved.
    scene = bpy.data.scenes.new('PRIVATE_SOURCE_AXIS_REVIEW')
    mesh = bpy.data.meshes.new('RAW_SOURCE_UNWELDED')
    mesh.from_pydata(vertices, [], [(i,i+1,i+2) for i in range(0,len(vertices),3)])
    mesh.update()
    obj = bpy.data.objects.new('RAW_SOURCE_UNMODIFIED_COORDINATES',mesh)
    scene.collection.objects.link(obj)
    if len(mesh.vertices)!=len(vertices) or len(mesh.polygons)!=diagnostic['raw_faces']:
        raise ValueError('Blender did not retain raw vertex/triangle counts')
    for vertex, expected in zip(mesh.vertices,vertices):
        if tuple(vertex.co)!=expected:
            raise ValueError('Blender changed a raw float32 coordinate')
    scene.render.engine='BLENDER_WORKBENCH'
    scene.display.shading.light='STUDIO'
    scene.display.shading.color_type='SINGLE'
    scene.display.shading.single_color=(0.75,0.62,0.38)
    scene.display.shading.background_type='VIEWPORT'
    scene.display.shading.background_color=(1,1,1)
    scene.render.resolution_x=scene.render.resolution_y=resolution
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    camera=bpy.data.objects.new('SOURCE_AXIS_CAMERA',bpy.data.cameras.new('SOURCE_AXIS_CAMERA'))
    scene.collection.objects.link(camera)
    scene.camera=camera
    camera.data.type='ORTHO'
    low=Vector(lo)
    high=Vector(hi)
    centre=(low+high)/2
    camera.data.ortho_scale=span*1.3
    camera.data.clip_start=max(span*0.00001,0.000001)
    camera.data.clip_end=span*6
    out.mkdir(parents=True,exist_ok=False)
    images=[]
    for label,direction,up in [('source_X',(1,0,0),'Z'),('source_Y',(0,1,0),'Z'),('source_Z',(0,0,1),'Y')]:
        camera.location=centre+Vector(direction)*span*3
        camera.rotation_euler=(centre-camera.location).to_track_quat('-Z',up).to_euler()
        path=out/(label+'.png')
        scene.render.filepath=str(path)
        bpy.ops.render.render(write_still=True,scene=scene.name)
        images.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    if hashlib.sha256(src.read_bytes()).hexdigest()!=digest:
        raise ValueError('Source bytes changed during review')
    report={'kind':'PRIVATE_UNREGISTERED_SOURCE_AXIS_BLENDER_REVIEW',
            'input_sha256':digest,'blender':bpy.app.version_string,
            'imported_raw_triangles':len(mesh.polygons),'imported_raw_vertex_instances':len(mesh.vertices),
            'raw_coordinates_exactly_preserved':True,'source_units_or_frame_verified':False,
            'anatomical_views_accepted':False,'canonical_promotion_allowed':False,
            'source_geometry_modified':False,'images':images}
    with (out/'review.json').open('x',encoding='utf-8') as fp:
        json.dump(report,fp,indent=2,sort_keys=True,allow_nan=False)
    return report


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input',required=True,type=Path)
    ap.add_argument('--sha256',required=True)
    ap.add_argument('--out',required=True,type=Path)
    args=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
    print(json.dumps(review(args.input,args.sha256,args.out)))
