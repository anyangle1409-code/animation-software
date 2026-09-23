"""Apply V7 sculpt to editable Blender asset and weld the paired knee UV seam.

The GLB intentionally keeps the per-island UV0 vertex split. Blender keeps UV0
per polygon corner, so paired geometric vertices can be one connected mesh.
"""
from pathlib import Path
import json,struct,sys
import bpy
import bmesh
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
version=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv and len(sys.argv)>sys.argv.index('--')+1 else 'v7_knee_retopology_rebuild'
blend=ROOT/f'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{version}.blend'
glb=ROOT/f'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{version}.glb'
seams=json.loads((ROOT/'reports/knee_seam_v5.json').read_text())['knees']
data=glb.read_bytes();n=struct.unpack_from('<I',data,12)[0]
doc=json.loads(data[20:20+n]);prim=doc['meshes'][0]['primitives'][0]
a=doc['accessors'][prim['attributes']['POSITION']];view=doc['bufferViews'][a['bufferView']]
pos=np.ndarray((a['count'],3),'<f4',buffer=data,
               offset=28+n+view.get('byteOffset',0)+a.get('byteOffset',0),
               strides=(view.get('byteStride',12),4)).copy()

bpy.ops.wm.open_mainfile(filepath=str(blend))
body=max((obj for obj in bpy.data.objects if obj.type=='MESH'),key=lambda obj:len(obj.data.vertices))
assert len(body.data.vertices)==len(pos)==33089
before_faces=len(body.data.polygons)
before_uv={uv.name:len(uv.data) for uv in body.data.uv_layers}
for i,v in enumerate(body.data.vertices):v.co=(float(pos[i,0]),float(-pos[i,2]),float(pos[i,1]))
body.data.update()

seam_ids={i for side in seams.values() for path in side['paths'] for i in path}
bm=bmesh.new();bm.from_mesh(body.data);bm.verts.ensure_lookup_table()
bmesh.ops.remove_doubles(bm,verts=[bm.verts[i] for i in seam_ids],dist=1e-6)
bm.to_mesh(body.data);bm.free();body.data.update()
assert len(body.data.vertices)==33059,len(body.data.vertices)
assert len(body.data.polygons)==before_faces
assert {uv.name:len(uv.data) for uv in body.data.uv_layers}==before_uv

body['candidate_only']=True
body['knee_retopology_note']='30 paired knee seam vertices welded in Blender; UV0 remains per face corner.'
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
report={'blend':blend.name,'body_vertices_before':33089,'body_vertices_after':len(body.data.vertices),
        'triangles_unchanged':len(body.data.polygons),'uv_loop_counts_unchanged':before_uv,
        'welded_pairs':30,'frozen_rig_objects_unedited':True}
(ROOT/f'reports/blend_topology_{version}.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
